"""Lógica de autenticación: registro, login, 2FA y recuperación.

Capa de servicio sin estado (puede instanciarse libremente). Encapsula:
  · registro de usuarios (con TOTP secret + recovery codes + recovery file)
  · login por contraseña (con o sin 2FA)
  · validación TOTP, recovery codes y recovery file
  · reset de contraseña vía email (token de un solo uso, 15 min)
  · login con Google (crear o vincular cuenta existente)

Reglas:
  · Las credenciales nunca se guardan en plaintext (werkzeug.scrypt + sha256).
  · Las consultas usan parámetros ligados.
  · Los errores de validación se lanzan como `AuthError(mensaje, campo)`.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import Config
from models.recovery import PasswordResetRepository, RecoveryCodeRepository
from models.usuario import Usuario, UsuarioRepository
from services import email_service, totp_service

logger = logging.getLogger(__name__)

# Reglas de validación
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
_NOMBRE_MIN = 2
_NOMBRE_MAX = 80
_PASSWORD_MIN = 8
_RECOVERY_CODES_TOTAL = 8
_RESET_TOKEN_TTL = timedelta(minutes=15)


class AuthError(Exception):
    """Error de validación o conflicto en operaciones de auth."""

    def __init__(self, mensaje: str, campo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


@dataclass(frozen=True, slots=True)
class DatosRegistro:
    nombres: str
    apellidos: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class ResultadoRegistro:
    usuario: Usuario
    totp_secret: str
    qr_data_url: str
    recovery_codes_plano: list[str]   # solo se devuelven UNA vez al cliente


@dataclass(frozen=True, slots=True)
class ResultadoLogin:
    usuario: Usuario
    requiere_2fa: bool


# ============================================================
# Servicio principal
# ============================================================

class AuthService:
    """Orquesta auth: usa los repos y los servicios auxiliares."""

    def __init__(
        self,
        usuarios: UsuarioRepository | None = None,
        recovery_codes: RecoveryCodeRepository | None = None,
        password_resets: PasswordResetRepository | None = None,
    ) -> None:
        self.usuarios = usuarios or UsuarioRepository()
        self.recovery = recovery_codes or RecoveryCodeRepository()
        self.resets = password_resets or PasswordResetRepository()

    # ---------- REGISTRO ----------
    def registrar(self, datos: DatosRegistro) -> ResultadoRegistro:
        nombres   = self._validar_nombre(datos.nombres,   "nombres")
        apellidos = self._validar_nombre(datos.apellidos, "apellidos")
        email     = self._validar_email(datos.email)
        self._validar_password(datos.password)

        if self.usuarios.existe_email(email):
            raise AuthError("Ese correo ya está registrado.", campo="email")

        # Credenciales y secretos
        password_hash    = generate_password_hash(datos.password)
        totp_secret      = totp_service.generar_secreto()
        recovery_codes   = _generar_recovery_codes(_RECOVERY_CODES_TOTAL)
        recovery_token   = secrets.token_urlsafe(32)
        recovery_f_hash  = _hash_token(recovery_token)

        user_id = self.usuarios.crear(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            password_hash=password_hash,
            totp_secret=totp_secret,
            recovery_file_hash=recovery_f_hash,
        )

        # Persiste los códigos hasheados
        self.recovery.reemplazar(
            user_id,
            [_hash_token(c) for c in recovery_codes],
        )

        # Email de bienvenida con archivo de recovery + códigos
        try:
            email_service.email_bienvenida(
                destinatario=email,
                nombres=nombres,
                recovery_token=recovery_token,
                recovery_codes=recovery_codes,
            )
        except email_service.EmailError as exc:
            logger.warning("No se envió email de bienvenida a %s: %s", email, exc)

        usuario = Usuario(
            id=user_id,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            totp_enabled=False,
        )
        return ResultadoRegistro(
            usuario=usuario,
            totp_secret=totp_secret,
            qr_data_url=totp_service.qr_data_url(totp_secret, email),
            recovery_codes_plano=recovery_codes,
        )

    # ---------- LOGIN ----------
    def login_password(self, email: str, password: str) -> ResultadoLogin:
        email = (email or "").strip().lower()
        if not (email and password):
            raise AuthError("Email y contraseña son obligatorios.")
        fila = self.usuarios.obtener_por_email(email)
        if not fila or not check_password_hash(fila["password_hash"], password):
            raise AuthError("Credenciales incorrectas.", campo="email")

        usuario = Usuario.desde_fila(fila)
        return ResultadoLogin(usuario=usuario, requiere_2fa=usuario.totp_enabled)

    def verificar_2fa(self, user_id: int, codigo: str) -> Usuario:
        fila = self.usuarios.obtener_por_id(user_id)
        if not fila or not fila.get("totp_secret"):
            raise AuthError("Usuario sin 2FA configurado.")
        if not totp_service.verificar_codigo(fila["totp_secret"], codigo):
            raise AuthError("Código de verificación incorrecto.")
        return Usuario.desde_fila(fila)

    def activar_2fa(self, user_id: int, codigo: str) -> None:
        """Llamado desde la pantalla de configuración de 2FA."""
        fila = self.usuarios.obtener_por_id(user_id)
        if not fila or not fila.get("totp_secret"):
            raise AuthError("Usuario inválido.")
        if not totp_service.verificar_codigo(fila["totp_secret"], codigo):
            raise AuthError("El código no coincide. Intenta de nuevo.")
        self.usuarios.activar_totp(user_id)

    # ---------- RECOVERY: códigos ----------
    def usar_recovery_code(self, user_id: int, codigo: str) -> Usuario:
        codigo = (codigo or "").strip().upper().replace(" ", "")
        if not codigo:
            raise AuthError("Ingresa un código de recuperación.")
        fila = self.usuarios.obtener_por_id(user_id)
        if not fila:
            raise AuthError("Usuario inválido.")

        codigo_hash = _hash_token(codigo)
        for activo in self.recovery.listar_activos(user_id):
            if hmac.compare_digest(activo["code_hash"], codigo_hash):
                self.recovery.marcar_usado(activo["id"])
                return Usuario.desde_fila(fila)
        raise AuthError("Ese código no es válido o ya fue usado.")

    # ---------- RECOVERY: archivo ----------
    def usar_recovery_file(self, user_id: int, contenido: str) -> Usuario:
        token = _extraer_token_de_archivo(contenido)
        if not token:
            raise AuthError("Archivo inválido: no se encontró el token.")

        fila = self.usuarios.obtener_por_id(user_id)
        if not fila or not fila.get("recovery_file_hash"):
            raise AuthError("Usuario sin archivo de recuperación.")
        if not hmac.compare_digest(fila["recovery_file_hash"], _hash_token(token)):
            raise AuthError("El archivo no coincide con esta cuenta.")
        return Usuario.desde_fila(fila)

    # ---------- RECOVERY: reset por email ----------
    def solicitar_reset_email(self, email: str) -> None:
        """Envía un email con un enlace de reset si el usuario existe.

        La función NO revela si el email está registrado (para no filtrar
        información). El llamador siempre recibe éxito.
        """
        email = (email or "").strip().lower()
        if not _EMAIL_RE.match(email):
            return  # silencioso

        fila = self.usuarios.obtener_por_email(email)
        if not fila:
            return  # silencioso, no revelar

        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        expira_en = datetime.now() + _RESET_TOKEN_TTL

        self.resets.invalidar_pendientes(fila["id"])
        self.resets.crear(fila["id"], token_hash, expira_en)

        link = f"{Config.APP_BASE_URL.rstrip('/')}/reset-password?token={token}"
        try:
            email_service.email_reset_password(
                destinatario=email,
                nombres=fila["nombres"],
                link=link,
            )
        except email_service.EmailError as exc:
            logger.warning("No se envió email de reset a %s: %s", email, exc)

    def confirmar_reset(self, token: str, nueva_password: str) -> None:
        if not token:
            raise AuthError("Token inválido.")
        self._validar_password(nueva_password)
        registro = self.resets.buscar_vigente(_hash_token(token))
        if not registro:
            raise AuthError("El enlace expiró o ya fue utilizado.")
        self.usuarios.actualizar_password(
            registro["usuario_id"],
            generate_password_hash(nueva_password),
        )
        self.resets.marcar_usado(registro["id"])

    # ---------- GOOGLE OAUTH ----------
    def login_o_registro_google(
        self,
        google_id: str,
        email: str,
        nombres: str,
        apellidos: str,
    ) -> Usuario:
        """Si la cuenta existe la vincula; si no, crea una nueva."""
        existing = self.usuarios.obtener_por_google_id(google_id)
        if existing:
            return Usuario.desde_fila(existing)

        # Vincula a una cuenta con el mismo email si ya estaba registrada
        por_email = self.usuarios.obtener_por_email(email)
        if por_email:
            self.usuarios.vincular_google(por_email["id"], google_id)
            por_email["google_id"] = google_id
            return Usuario.desde_fila(por_email)

        # Crear nueva cuenta sin password (usuario solo entra por Google)
        password_hash = generate_password_hash(secrets.token_urlsafe(24))
        user_id = self.usuarios.crear(
            nombres=nombres or "Usuario",
            apellidos=apellidos or "",
            email=email,
            password_hash=password_hash,
            google_id=google_id,
            email_verified=True,
        )
        return Usuario(
            id=user_id,
            nombres=nombres or "Usuario",
            apellidos=apellidos or "",
            email=email,
        )

    # ---------- VALIDADORES ----------
    @staticmethod
    def _validar_nombre(valor: str, campo: str) -> str:
        valor = (valor or "").strip()
        if len(valor) < _NOMBRE_MIN:
            raise AuthError(
                f"El campo '{campo}' debe tener al menos {_NOMBRE_MIN} caracteres.",
                campo=campo,
            )
        if len(valor) > _NOMBRE_MAX:
            raise AuthError(
                f"El campo '{campo}' no puede exceder {_NOMBRE_MAX} caracteres.",
                campo=campo,
            )
        return valor

    @staticmethod
    def _validar_email(valor: str) -> str:
        valor = (valor or "").strip().lower()
        if not _EMAIL_RE.match(valor):
            raise AuthError("Correo electrónico no válido.", campo="email")
        if len(valor) > 120:
            raise AuthError("El correo es demasiado largo.", campo="email")
        return valor

    @staticmethod
    def _validar_password(valor: str) -> None:
        if not valor or len(valor) < _PASSWORD_MIN:
            raise AuthError(
                f"La contraseña debe tener al menos {_PASSWORD_MIN} caracteres.",
                campo="password",
            )
        if not (re.search(r"[A-Za-z]", valor) and re.search(r"\d", valor)):
            raise AuthError(
                "La contraseña debe contener letras y números.",
                campo="password",
            )


# ============================================================
# Helpers
# ============================================================

def _generar_recovery_codes(cantidad: int) -> list[str]:
    """Genera códigos formato XXXX-XXXX (mayúsculas, sin caracteres ambiguos)."""
    abecedario = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    codes = []
    for _ in range(cantidad):
        a = "".join(secrets.choice(abecedario) for _ in range(4))
        b = "".join(secrets.choice(abecedario) for _ in range(4))
        codes.append(f"{a}-{b}")
    return codes


def _hash_token(token: str) -> str:
    """SHA-256 hex con sal fija basada en SECRET_KEY (HMAC-style)."""
    key = (Config.SECRET_KEY or "salt").encode("utf-8")
    return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()


def _extraer_token_de_archivo(contenido: str) -> str | None:
    """Busca la línea `Token: ...` dentro del archivo recovery.txt."""
    if not contenido:
        return None
    for linea in contenido.splitlines():
        linea = linea.strip()
        if linea.lower().startswith("token:"):
            return linea.split(":", 1)[1].strip()
    return None
