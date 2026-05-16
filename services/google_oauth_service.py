"""Servicio de OAuth con Google para 'Iniciar sesión con Google'.

Usa Authlib (sobre `requests`) para no acoplar a Flask-Dance ni similares.
Flujo:
  1) `iniciar_flujo()` genera la URL de autorización + un `state` que el
     llamador debe persistir en la sesión.
  2) Tras el redirect, `intercambiar_codigo()` valida el state, intercambia
     el `code` por un token y devuelve la información del usuario.
"""
from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass

import requests

from config.settings import Config

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthError(Exception):
    """Error genérico del flujo OAuth."""


@dataclass(frozen=True, slots=True)
class GoogleProfile:
    sub: str         # google_id (estable)
    email: str
    nombres: str
    apellidos: str
    email_verified: bool


def _config_ok() -> bool:
    return bool(Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET)


def iniciar_flujo() -> tuple[str, str]:
    """Devuelve (url_autorizacion, state). Guarda `state` en la sesión Flask."""
    if not _config_ok():
        raise GoogleOAuthError(
            "Google OAuth no configurado. Define GOOGLE_CLIENT_ID y "
            "GOOGLE_CLIENT_SECRET en .env"
        )

    state = secrets.token_urlsafe(24)
    params = {
        "client_id":     Config.GOOGLE_CLIENT_ID,
        "redirect_uri":  Config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    qs = "&".join(f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{qs}", state


def intercambiar_codigo(code: str, state_recibido: str, state_esperado: str) -> GoogleProfile:
    """Intercambia el `code` por un access_token y obtiene el perfil."""
    if not state_recibido or state_recibido != state_esperado:
        raise GoogleOAuthError("State inválido o expirado.")

    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id":     Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "code":          code,
            "grant_type":    "authorization_code",
            "redirect_uri":  Config.GOOGLE_REDIRECT_URI,
        },
        timeout=10,
    )
    if token_resp.status_code != 200:
        raise GoogleOAuthError(f"Token endpoint error: {token_resp.text}")
    access_token = token_resp.json().get("access_token")
    if not access_token:
        raise GoogleOAuthError("Google no devolvió access_token.")

    user_resp = requests.get(
        GOOGLE_USER_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if user_resp.status_code != 200:
        raise GoogleOAuthError(f"Userinfo endpoint error: {user_resp.text}")

    info = user_resp.json()
    return GoogleProfile(
        sub=str(info.get("id") or info.get("sub") or ""),
        email=info.get("email", ""),
        nombres=info.get("given_name") or "",
        apellidos=info.get("family_name") or "",
        email_verified=bool(info.get("verified_email", False)),
    )
