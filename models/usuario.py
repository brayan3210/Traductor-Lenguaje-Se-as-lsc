"""Capa de acceso a datos para los usuarios registrados.

Sigue el mismo patrón que `DiccionarioRepository`: parámetros ligados,
context managers y consultas SQL parametrizadas para evitar inyección.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from database.connection import get_cursor

logger = logging.getLogger(__name__)


# La tabla se crea idempotentemente al arrancar la app, así el usuario
# no necesita ejecutar migraciones manuales.
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    nombres              VARCHAR(80)  NOT NULL,
    apellidos            VARCHAR(80)  NOT NULL,
    email                VARCHAR(120) NOT NULL UNIQUE,
    password_hash        VARCHAR(255) NOT NULL,
    totp_secret          VARCHAR(64)  NULL,
    totp_enabled         TINYINT(1)   NOT NULL DEFAULT 0,
    recovery_file_hash   VARCHAR(255) NULL,
    google_id            VARCHAR(64)  NULL,
    email_verified       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email     (email),
    INDEX idx_google_id (google_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

# Migración suave: agrega columnas si la tabla ya existía con un esquema antiguo.
_ADD_COLUMNS_SQL = [
    "ALTER TABLE usuarios ADD COLUMN totp_secret VARCHAR(64) NULL",
    "ALTER TABLE usuarios ADD COLUMN totp_enabled TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE usuarios ADD COLUMN recovery_file_hash VARCHAR(255) NULL",
    "ALTER TABLE usuarios ADD COLUMN google_id VARCHAR(64) NULL",
    "ALTER TABLE usuarios ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0",
]


@dataclass(frozen=True, slots=True)
class Usuario:
    """Representación pública (sin credenciales) de un usuario."""
    id: int
    nombres: str
    apellidos: str
    email: str
    totp_enabled: bool = False

    @classmethod
    def desde_fila(cls, row: dict[str, Any]) -> "Usuario":
        return cls(
            id=int(row["id"]),
            nombres=row["nombres"],
            apellidos=row["apellidos"],
            email=row["email"],
            totp_enabled=bool(row.get("totp_enabled", 0)),
        )


class UsuarioRepository:
    """Operaciones sobre la tabla `usuarios`."""

    # ---------- Esquema ----------
    def asegurar_tabla(self) -> None:
        """Crea la tabla si no existe e intenta migrar columnas faltantes."""
        with get_cursor(commit=True) as cursor:
            cursor.execute(_CREATE_TABLE_SQL)
            for stmt in _ADD_COLUMNS_SQL:
                try:
                    cursor.execute(stmt)
                except Exception:
                    # Columna ya existe → ignorar silenciosamente.
                    pass

    # ---------- Lecturas ----------
    def existe_email(self, email: str) -> bool:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM usuarios WHERE email = %s LIMIT 1",
                (email,),
            )
            return cursor.fetchone() is not None

    def obtener_por_email(self, email: str) -> dict[str, Any] | None:
        """Devuelve la fila completa o None."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s LIMIT 1",
                (email,),
            )
            return cursor.fetchone()

    def obtener_por_id(self, user_id: int) -> dict[str, Any] | None:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE id = %s LIMIT 1",
                (user_id,),
            )
            return cursor.fetchone()

    def obtener_por_google_id(self, google_id: str) -> dict[str, Any] | None:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE google_id = %s LIMIT 1",
                (google_id,),
            )
            return cursor.fetchone()

    # ---------- Escritura ----------
    def crear(
        self,
        nombres: str,
        apellidos: str,
        email: str,
        password_hash: str,
        totp_secret: str | None = None,
        recovery_file_hash: str | None = None,
        google_id: str | None = None,
        email_verified: bool = False,
    ) -> int:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO usuarios "
                "(nombres, apellidos, email, password_hash, totp_secret, "
                " recovery_file_hash, google_id, email_verified) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    nombres, apellidos, email, password_hash, totp_secret,
                    recovery_file_hash, google_id, 1 if email_verified else 0,
                ),
            )
            return cursor.lastrowid

    def actualizar_password(self, user_id: int, password_hash: str) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                (password_hash, user_id),
            )

    def activar_totp(self, user_id: int) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE usuarios SET totp_enabled = 1 WHERE id = %s",
                (user_id,),
            )

    def vincular_google(self, user_id: int, google_id: str) -> None:
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE usuarios SET google_id = %s, email_verified = 1 "
                "WHERE id = %s",
                (google_id, user_id),
            )
