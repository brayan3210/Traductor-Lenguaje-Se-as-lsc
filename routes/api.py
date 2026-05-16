"""API REST del traductor LSC.

Endpoints:
    POST /api/traducir              → traduce texto a secuencia de señas
    GET  /api/diccionario           → lista entradas (con filtros opcionales)
    GET  /api/diccionario/buscar    → búsqueda por fragmento
    GET  /api/diccionario/categorias→ lista de categorías
    GET  /api/stats                 → estadísticas de cobertura
    GET  /api/historial             → traducciones recientes
    GET  /api/salud                 → health check de DB y NLP
"""
from __future__ import annotations

import logging

import pymysql
from flask import Blueprint, jsonify, redirect, request, session, url_for

from database.connection import check_connection
from models.diccionario import DiccionarioRepository, HistorialRepository
from services.auth_service import AuthError, AuthService, DatosRegistro
from services.chat_service import get_chat_service
from services.google_oauth_service import (
    GoogleOAuthError,
    intercambiar_codigo as google_intercambiar,
    iniciar_flujo as google_iniciar,
)
from services.media_resolver import resolver as resolver_media
from services.nlp_service import NLPService
from services.traductor_service import TraductorService

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

_diccionario_repo = DiccionarioRepository()
_historial_repo = HistorialRepository()
_nlp_service = NLPService()
_traductor_service = TraductorService(
    nlp=_nlp_service,
    diccionario=_diccionario_repo,
    historial=_historial_repo,
)
_auth_service = AuthService()

MAX_TEXTO_LEN = 2000


def _ip_cliente() -> str | None:
    return request.headers.get("X-Forwarded-For") or request.remote_addr


def _error(mensaje: str, status: int = 400, **extra):
    payload = {"success": False, "error": mensaje}
    payload.update(extra)
    return jsonify(payload), status


# ---------- POST /api/traducir ----------
@api_bp.post("/traducir")
def traducir():
    data = request.get_json(silent=True) or {}
    texto = (data.get("texto") or "").strip()

    if not texto:
        return _error("El campo 'texto' es obligatorio y no puede estar vacío.")
    if len(texto) > MAX_TEXTO_LEN:
        return _error(
            f"El texto excede el máximo permitido de {MAX_TEXTO_LEN} caracteres.",
            status=413,
        )

    try:
        resultado = _traductor_service.traducir(texto, ip_cliente=_ip_cliente())
    except pymysql.MySQLError:
        logger.exception("Error de base de datos en /api/traducir")
        return _error("La base de datos no respondió. Intenta más tarde.", status=503)
    except RuntimeError as exc:
        logger.exception("Error NLP en /api/traducir")
        return _error(str(exc), status=500)

    return jsonify(resultado.as_dict())


# ---------- GET /api/diccionario ----------
def _resolver_entradas(entradas: list[dict]) -> list[dict]:
    """Aplica el resolver de media a cada entrada del diccionario.

    Actualiza `gif_url` con la URL real en disco (preferencia .mp4 → .gif)
    y agrega `media_type` y `existe` para que el frontend sepa si usar
    `<video>` o `<img>` y si debe mostrar el fallback de archivo perdido.
    """
    for e in entradas:
        media = resolver_media(e.get("gif_url", ""))
        e["gif_url"]     = media.url
        e["media_type"]  = media.media_type
        e["existe"]      = media.existe
    return entradas


@api_bp.get("/diccionario")
def listar_diccionario():
    categoria = request.args.get("categoria")
    tipo = request.args.get("tipo")
    entradas = _diccionario_repo.listar(categoria=categoria, tipo=tipo)
    entradas = _resolver_entradas(entradas)
    return jsonify(
        {
            "success": True,
            "total": len(entradas),
            "entradas": entradas,
        }
    )


@api_bp.get("/diccionario/buscar")
def buscar_diccionario():
    consulta = (request.args.get("q") or "").strip()
    if not consulta:
        return _error("El parámetro 'q' es obligatorio.")
    if len(consulta) > 80:
        return _error("Consulta demasiado larga.")
    entradas = _diccionario_repo.listar(buscar=consulta)
    entradas = _resolver_entradas(entradas)
    return jsonify(
        {
            "success": True,
            "consulta": consulta,
            "total": len(entradas),
            "entradas": entradas,
        }
    )


@api_bp.get("/diccionario/categorias")
def listar_categorias():
    return jsonify(
        {
            "success": True,
            "categorias": _diccionario_repo.listar_categorias(),
        }
    )


# ---------- GET /api/stats ----------
@api_bp.get("/stats")
def stats():
    resumen = _diccionario_repo.estadisticas()
    resumen["total_traducciones"] = _historial_repo.total()
    resumen["desglose"] = _diccionario_repo.contar_por_categoria()
    return jsonify({"success": True, **resumen})


# ---------- GET /api/historial ----------
@api_bp.get("/historial")
def historial():
    try:
        limite = int(request.args.get("limite", 10))
    except (TypeError, ValueError):
        limite = 10
    return jsonify(
        {
            "success": True,
            "registros": _historial_repo.recientes(limite=limite),
            "total": _historial_repo.total(),
        }
    )


# ============================================================
# AUTENTICACIÓN
# ============================================================

def _serializar_usuario(usuario) -> dict:
    return {
        "id":           usuario.id,
        "nombres":      usuario.nombres,
        "apellidos":    usuario.apellidos,
        "email":        usuario.email,
        "totp_enabled": usuario.totp_enabled,
    }


def _crear_sesion(user_id: int) -> None:
    session.clear()
    session["user_id"] = user_id
    session["pending_2fa"] = False
    session.permanent = True


# ---------- POST /api/registro ----------
@api_bp.post("/registro")
def registro():
    data = request.get_json(silent=True) or {}
    try:
        datos = DatosRegistro(
            nombres=str(data.get("nombres", "")),
            apellidos=str(data.get("apellidos", "")),
            email=str(data.get("email", "")),
            password=str(data.get("password", "")),
        )
        resultado = _auth_service.registrar(datos)
    except AuthError as exc:
        return _error(exc.mensaje, status=400, campo=exc.campo)
    except pymysql.MySQLError:
        logger.exception("Error de base de datos en /api/registro")
        return _error("La base de datos no respondió. Intenta más tarde.", status=503)

    # Inicia sesión "a medio camino": el usuario autenticado pero pendiente
    # de configurar 2FA. Su user_id queda en la sesión para mostrar el QR.
    session.clear()
    session["user_id"] = resultado.usuario.id
    session["pending_2fa"] = False
    session["just_registered"] = True
    session.permanent = True

    return jsonify({
        "success": True,
        "mensaje": "Cuenta creada correctamente. Te enviamos los datos de recuperación a tu correo.",
        "usuario": _serializar_usuario(resultado.usuario),
        "next":    "/setup-2fa",
    }), 201


# ---------- POST /api/login ----------
@api_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", ""))
    password = str(data.get("password", ""))

    try:
        resultado = _auth_service.login_password(email, password)
    except AuthError as exc:
        return _error(exc.mensaje, status=401, campo=exc.campo)
    except pymysql.MySQLError:
        logger.exception("Error de BD en /api/login")
        return _error("La base de datos no respondió.", status=503)

    session.clear()
    session["user_id"] = resultado.usuario.id
    session["pending_2fa"] = resultado.requiere_2fa
    session.permanent = True

    return jsonify({
        "success":      True,
        "usuario":      _serializar_usuario(resultado.usuario),
        "requiere_2fa": resultado.requiere_2fa,
        "next":         "/login/2fa" if resultado.requiere_2fa else "/",
    })


# ---------- POST /api/login/2fa ----------
@api_bp.post("/login/2fa")
def login_2fa():
    user_id = session.get("user_id")
    if not user_id or not session.get("pending_2fa"):
        return _error("No hay un login en curso.", status=401)

    codigo = (request.get_json(silent=True) or {}).get("codigo", "")
    try:
        usuario = _auth_service.verificar_2fa(user_id, str(codigo))
    except AuthError as exc:
        return _error(exc.mensaje, status=401)

    session["pending_2fa"] = False
    return jsonify({"success": True, "usuario": _serializar_usuario(usuario), "next": "/"})


# ---------- POST /api/login/recovery-code ----------
@api_bp.post("/login/recovery-code")
def login_recovery_code():
    user_id = session.get("user_id")
    if not user_id or not session.get("pending_2fa"):
        return _error("No hay un login en curso.", status=401)
    codigo = (request.get_json(silent=True) or {}).get("codigo", "")
    try:
        usuario = _auth_service.usar_recovery_code(user_id, str(codigo))
    except AuthError as exc:
        return _error(exc.mensaje, status=401)
    session["pending_2fa"] = False
    return jsonify({"success": True, "usuario": _serializar_usuario(usuario), "next": "/"})


# ---------- POST /api/login/recovery-file ----------
@api_bp.post("/login/recovery-file")
def login_recovery_file():
    user_id = session.get("user_id")
    if not user_id or not session.get("pending_2fa"):
        return _error("No hay un login en curso.", status=401)
    archivo = request.files.get("archivo")
    if not archivo:
        return _error("Debes adjuntar el archivo de recuperación.")
    contenido = archivo.read().decode("utf-8", errors="ignore")
    try:
        usuario = _auth_service.usar_recovery_file(user_id, contenido)
    except AuthError as exc:
        return _error(exc.mensaje, status=401)
    session["pending_2fa"] = False
    return jsonify({"success": True, "usuario": _serializar_usuario(usuario), "next": "/"})


# ---------- POST /api/forgot-password ----------
@api_bp.post("/forgot-password")
def forgot_password():
    email = (request.get_json(silent=True) or {}).get("email", "")
    _auth_service.solicitar_reset_email(str(email))
    # Respuesta neutra siempre: no se revela si existe la cuenta.
    return jsonify({
        "success": True,
        "mensaje": "Si el correo está registrado, te enviamos las instrucciones.",
    })


# ---------- POST /api/reset-password ----------
@api_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = str(data.get("token", ""))
    password = str(data.get("password", ""))
    try:
        _auth_service.confirmar_reset(token, password)
    except AuthError as exc:
        return _error(exc.mensaje, status=400, campo=exc.campo)
    return jsonify({"success": True, "mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."})


# ---------- 2FA SETUP ----------
@api_bp.get("/2fa/setup")
def setup_2fa_data():
    user_id = session.get("user_id")
    if not user_id:
        return _error("Inicia sesión primero.", status=401)
    fila = _auth_service.usuarios.obtener_por_id(user_id)
    if not fila:
        return _error("Usuario no encontrado.", status=404)

    from services import totp_service as _totp
    secreto = fila.get("totp_secret")
    if not secreto:
        secreto = _totp.generar_secreto()
        # Si el usuario no tenía secreto (caso raro), asignar uno
        # — no se persiste hasta que active 2FA, por simplicidad.
    qr = _totp.qr_data_url(secreto, fila["email"])
    return jsonify({
        "success":      True,
        "secret":       secreto,
        "qr_data_url":  qr,
        "totp_enabled": bool(fila.get("totp_enabled", 0)),
    })


@api_bp.post("/2fa/activar")
def activar_2fa():
    user_id = session.get("user_id")
    if not user_id:
        return _error("Inicia sesión primero.", status=401)
    codigo = (request.get_json(silent=True) or {}).get("codigo", "")
    try:
        _auth_service.activar_2fa(user_id, str(codigo))
    except AuthError as exc:
        return _error(exc.mensaje, status=400)
    return jsonify({"success": True, "mensaje": "2FA activado correctamente."})


# ---------- LOGOUT ----------
@api_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "next": "/"})


# ---------- GOOGLE OAUTH ----------
@api_bp.get("/auth/google")
def google_login_inicio():
    try:
        url, state = google_iniciar()
    except GoogleOAuthError as exc:
        return _error(str(exc), status=503)
    session["google_oauth_state"] = state
    return redirect(url)


@api_bp.get("/auth/google/callback")
def google_login_callback():
    code  = request.args.get("code", "")
    state = request.args.get("state", "")
    state_esperado = session.pop("google_oauth_state", "")
    try:
        perfil = google_intercambiar(code, state, state_esperado)
        usuario = _auth_service.login_o_registro_google(
            google_id=perfil.sub,
            email=perfil.email,
            nombres=perfil.nombres,
            apellidos=perfil.apellidos,
        )
    except GoogleOAuthError as exc:
        logger.exception("Fallo Google OAuth")
        return redirect(url_for("main.login") + f"?error={str(exc)[:80]}")

    session.clear()
    session["user_id"]     = usuario.id
    session["pending_2fa"] = False
    session.permanent = True
    return redirect(url_for("main.index"))


# ---------- /api/me ----------
@api_bp.get("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return _error("No autenticado.", status=401)
    fila = _auth_service.usuarios.obtener_por_id(user_id)
    if not fila:
        session.clear()
        return _error("Sesión inválida.", status=401)
    from models.usuario import Usuario as _U
    return jsonify({"success": True, "usuario": _serializar_usuario(_U.desde_fila(fila))})


# ---------- POST /api/chat ----------
@api_bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    mensaje = (data.get("mensaje") or "").strip()
    if not mensaje:
        return _error("El campo 'mensaje' es obligatorio.")
    if len(mensaje) > 1000:
        return _error("El mensaje excede 1000 caracteres.", status=413)

    try:
        respuesta = get_chat_service().responder(mensaje)
    except RuntimeError as exc:
        logger.exception("Modelo de chat no disponible")
        return _error(str(exc), status=503)
    except Exception:
        logger.exception("Error al generar respuesta del chat")
        return _error("No se pudo generar una respuesta.", status=500)

    return jsonify({"success": True, "respuesta": respuesta})


# ---------- GET /api/salud ----------
@api_bp.get("/salud")
def salud():
    db_ok = check_connection()
    try:
        _ = _nlp_service.nlp
        nlp_ok = True
        nlp_mensaje = None
    except RuntimeError as exc:
        nlp_ok = False
        nlp_mensaje = str(exc)

    status = 200 if (db_ok and nlp_ok) else 503
    return (
        jsonify(
            {
                "success": db_ok and nlp_ok,
                "db": {"ok": db_ok},
                "nlp": {"ok": nlp_ok, "mensaje": nlp_mensaje},
            }
        ),
        status,
    )
