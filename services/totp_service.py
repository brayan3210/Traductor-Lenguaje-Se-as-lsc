"""Servicio TOTP (Google Authenticator / Authy / 1Password / etc.).

Genera el secreto base32, construye la URI estándar `otpauth://` para
que el usuario escanee el QR y valida los códigos de 6 dígitos.
"""
from __future__ import annotations

import base64
import io
import logging

import pyotp
import qrcode

from config.settings import Config

logger = logging.getLogger(__name__)


def generar_secreto() -> str:
    """Crea un secreto TOTP base32 (128 bits de entropía)."""
    return pyotp.random_base32()


def uri_provisioning(secreto: str, email: str) -> str:
    """Devuelve la URI `otpauth://` para construir el QR."""
    return pyotp.totp.TOTP(secreto).provisioning_uri(
        name=email,
        issuer_name=Config.TOTP_ISSUER,
    )


def qr_data_url(secreto: str, email: str) -> str:
    """Genera el QR como data URL (PNG en base64) listo para `<img src>`."""
    uri = uri_provisioning(secreto, email)
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def verificar_codigo(secreto: str, codigo: str, ventana: int = 1) -> bool:
    """Verifica un código de 6 dígitos. Una ventana de 1 = ±30 s de tolerancia."""
    if not (secreto and codigo):
        return False
    codigo = codigo.replace(" ", "").strip()
    if not codigo.isdigit() or len(codigo) != 6:
        return False
    return pyotp.TOTP(secreto).verify(codigo, valid_window=ventana)
