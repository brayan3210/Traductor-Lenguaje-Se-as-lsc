"""Repositorios para los mecanismos de recuperación de cuenta.

Tablas que se gestionan aquí:
  - recovery_codes        — códigos de un solo uso (estilo Google).
  - password_reset_tokens — tokens enviados por email para resetear pass.

Tanto los códigos como los tokens se guardan **hasheados** (nunca en
texto plano) para que un volcado de la BD no exponga credenciales.
"""
from __future__ import annotations

import logging
from typing import Any

from database.connection import get_cursor

logger = logging.getLogger(__name__)


_CREATE_RECOVERY_CODES_SQL = """
CREATE TABLE IF NOT EXISTS recovery_codes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT          NOT NULL,
    code_hash   VARCHAR(255) NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at     DATETIME     NULL,
    INDEX idx_usuario (usuario_id),
    CONSTRAINT fk_recovery_user
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_CREATE_PASSWORD_RESET_SQL = """
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT          NOT NULL,
    token_hash  VARCHAR(255) NOT NULL,
    expira_en   DATETIME     NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuario_pwd (usuario_id),
    CONSTRAINT fk_pwdreset_user
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


class RecoveryCodeRepository:
    """Códigos de un solo uso para acceder cuando se pierde el 2FA."""

    def asegurar_tabla(self) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(_CREATE_RECOVERY_CODES_SQL)

    def reemplazar(self, usuario_id: int, code_hashes: list[str]) -> None:
        """Borra los códigos previos y guarda los nuevos en bloque."""
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM recovery_codes WHERE usuario_id = %s",
                (usuario_id,),
            )
            cursor.executemany(
                "INSERT INTO recovery_codes (usuario_id, code_hash) VALUES (%s, %s)",
                [(usuario_id, h) for h in code_hashes],
            )

    def listar_activos(self, usuario_id: int) -> list[dict[str, Any]]:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id, code_hash FROM recovery_codes "
                "WHERE usuario_id = %s AND usado = 0",
                (usuario_id,),
            )
            return list(cursor.fetchall())

    def marcar_usado(self, code_id: int) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE recovery_codes SET usado = 1, used_at = NOW() "
                "WHERE id = %s",
                (code_id,),
            )


class PasswordResetRepository:
    """Tokens enviados por email para reiniciar la contraseña."""

    def asegurar_tabla(self) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(_CREATE_PASSWORD_RESET_SQL)

    def crear(self, usuario_id: int, token_hash: str, expira_en) -> int:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO password_reset_tokens "
                "(usuario_id, token_hash, expira_en) VALUES (%s, %s, %s)",
                (usuario_id, token_hash, expira_en),
            )
            return cursor.lastrowid

    def buscar_vigente(self, token_hash: str) -> dict[str, Any] | None:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id, usuario_id, expira_en, usado "
                "FROM password_reset_tokens "
                "WHERE token_hash = %s AND usado = 0 AND expira_en > NOW() "
                "LIMIT 1",
                (token_hash,),
            )
            return cursor.fetchone()

    def marcar_usado(self, token_id: int) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE password_reset_tokens SET usado = 1 WHERE id = %s",
                (token_id,),
            )

    def invalidar_pendientes(self, usuario_id: int) -> None:
        """Anula tokens previos para que solo el último sea válido."""
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE password_reset_tokens SET usado = 1 "
                "WHERE usuario_id = %s AND usado = 0",
                (usuario_id,),
            )
