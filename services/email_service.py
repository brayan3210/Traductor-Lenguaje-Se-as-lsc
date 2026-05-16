"""Servicio de envío de correo vía SMTP (Gmail con App Password).

Encapsula `smtplib` para que el resto de la app solo tenga que llamar a
`enviar_correo(...)` o a los helpers específicos (bienvenida, reset, etc.).
Todos los errores se loguean pero no se propagan al usuario final con
detalles internos.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from config.settings import Config

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Falla controlada al enviar un correo."""


def _cliente_smtp() -> smtplib.SMTP:
    if not (Config.SMTP_USER and Config.SMTP_APP_PASSWORD):
        raise EmailError("SMTP no configurado: revisa SMTP_USER y SMTP_APP_PASSWORD en .env")
    cliente = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20)
    cliente.ehlo()
    cliente.starttls()
    cliente.login(Config.SMTP_USER, Config.SMTP_APP_PASSWORD)
    return cliente


def enviar_correo(
    destinatario: str,
    asunto: str,
    cuerpo_html: str,
    cuerpo_texto: str | None = None,
    adjuntos: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """Envía un email simple o con adjuntos.

    `adjuntos` es una lista de `(nombre_archivo, contenido_bytes, mimetype)`.
    """
    msg = EmailMessage()
    msg["From"] = formataddr((Config.SMTP_FROM_NAME, Config.SMTP_USER))
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(cuerpo_texto or _strip_html(cuerpo_html))
    msg.add_alternative(cuerpo_html, subtype="html")

    for nombre, blob, mime in adjuntos or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(
            blob,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=nombre,
        )

    try:
        with _cliente_smtp() as cliente:
            cliente.send_message(msg)
        logger.info("Email enviado a %s asunto=%r", destinatario, asunto)
    except Exception as exc:
        logger.exception("Error enviando email a %s", destinatario)
        raise EmailError(str(exc)) from exc


def _strip_html(html: str) -> str:
    """Plain-text fallback muy simple para clientes que no soportan HTML."""
    import re
    text = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# ============================================================
# Templates específicos
# ============================================================

def email_bienvenida(
    destinatario: str,
    nombres: str,
    recovery_token: str,
    recovery_codes: list[str],
) -> None:
    """Email de bienvenida + adjunta el archivo de recuperación + códigos."""
    asunto = "Bienvenido a Señas Co · Datos de recuperación"

    codes_html = "".join(f"<li><code>{c}</code></li>" for c in recovery_codes)

    html = f"""\
<!DOCTYPE html>
<html><body style="font-family: 'Segoe UI', Arial, sans-serif; background:#0b1220; color:#f1f5f9; padding:0; margin:0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1220; padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#172338; border-radius:16px; border:1px solid rgba(148,163,184,0.16); overflow:hidden;">
        <tr><td style="padding:32px 36px; border-bottom:1px solid rgba(148,163,184,0.12);">
          <h1 style="margin:0; font-size:22px; color:#f1f5f9;">Hola {nombres} 👋</h1>
          <p style="margin:8px 0 0; color:#aab6c8;">Bienvenido a <strong>Señas Co</strong>.</p>
        </td></tr>
        <tr><td style="padding:28px 36px; color:#f1f5f9; line-height:1.6;">
          <p>Tu cuenta fue creada correctamente. Te enviamos este correo con tus <strong>datos de recuperación</strong>:</p>
          <h3 style="color:#93c5fd; margin:24px 0 12px;">📎 Archivo de recuperación</h3>
          <p>Adjuntamos un archivo <code>recovery.txt</code>. Guárdalo en un lugar seguro (memoria USB, gestor de claves). Si pierdes acceso a todo lo demás, súbelo en la pantalla de recuperación.</p>
          <h3 style="color:#93c5fd; margin:24px 0 12px;">🔢 Códigos de recuperación de un solo uso</h3>
          <p>Cada código sirve <strong>una sola vez</strong> para entrar sin tu autenticador. Imprímelos o cópialos:</p>
          <ul style="font-family: 'Courier New', monospace; font-size:15px; background:#0b1220; padding:18px 28px; border-radius:10px; list-style:none; margin:0;">
            {codes_html}
          </ul>
          <h3 style="color:#93c5fd; margin:24px 0 12px;">🔐 Configurar 2FA</h3>
          <p>Recuerda configurar Google Authenticator desde la pantalla de "Configurar 2FA" para proteger tu cuenta.</p>
        </td></tr>
        <tr><td style="padding:18px 36px; background:#0b1220; color:#7f8ba0; font-size:12px; text-align:center;">
          Este correo fue enviado por Señas Co · No respondas a esta dirección.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    recovery_filename = f"recovery_{nombres.lower().replace(' ', '_')}.txt"
    recovery_blob = (
        "==============================================\n"
        "  Señas Co — Archivo de recuperación de cuenta\n"
        "==============================================\n\n"
        f"Usuario: {destinatario}\n"
        f"Token:   {recovery_token}\n\n"
        "Sube este archivo en la pantalla de recuperación si\n"
        "pierdes acceso a tu autenticador y a tus códigos.\n"
        "NO compartas este archivo con nadie.\n"
    ).encode("utf-8")

    enviar_correo(
        destinatario=destinatario,
        asunto=asunto,
        cuerpo_html=html,
        adjuntos=[(recovery_filename, recovery_blob, "text/plain")],
    )


def email_reset_password(destinatario: str, nombres: str, link: str) -> None:
    asunto = "Señas Co · Restablece tu contraseña"
    html = f"""\
<!DOCTYPE html>
<html><body style="font-family: 'Segoe UI', Arial, sans-serif; background:#0b1220; color:#f1f5f9; margin:0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1220; padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#172338; border-radius:16px; border:1px solid rgba(148,163,184,0.16);">
        <tr><td style="padding:32px 36px;">
          <h1 style="margin:0; font-size:22px;">Hola {nombres}</h1>
          <p style="color:#aab6c8;">Recibimos una solicitud para restablecer tu contraseña en Señas Co.</p>
          <p style="margin:24px 0;">
            <a href="{link}" style="display:inline-block; padding:12px 24px; background:linear-gradient(135deg,#3b82f6,#14b8a6); color:white; text-decoration:none; border-radius:10px; font-weight:600;">
              Crear nueva contraseña
            </a>
          </p>
          <p style="color:#7f8ba0; font-size:13px;">El enlace caduca en 15 minutos. Si no fuiste tú, puedes ignorar este mensaje.</p>
          <p style="color:#7f8ba0; font-size:12px; word-break:break-all;">{link}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    enviar_correo(destinatario=destinatario, asunto=asunto, cuerpo_html=html)
