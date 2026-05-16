"""Gestión de conexiones MySQL con context managers.

Usa PyMySQL (driver puro en Python, compatible con XAMPP) y expone un
context manager `get_connection` que garantiza cierre de recursos.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from config.settings import Config

logger = logging.getLogger(__name__)

# Singleton de conexión perezosa: en desarrollo una conexión por request
# es suficiente; si se necesita pooling, basta con sustituir este módulo
# por dbutils.PooledDB sin tocar el resto del código.


def _build_connection() -> Connection:
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET,
        cursorclass=DictCursor,
        autocommit=False,
    )


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Abre una conexión MySQL y la cierra al finalizar el bloque."""
    conn = _build_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(commit: bool = False) -> Iterator[DictCursor]:
    """Atajo: abre conexión y entrega un cursor. Commit opcional al final."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def init_pool() -> None:
    """Stub para compatibilidad con el factory de la app.

    Permite migrar a pooling sin cambiar el punto de llamada.
    """
    logger.debug("Conexión MySQL inicializada en modo on-demand")


def close_pool() -> None:
    """Stub: no hay pool persistente en esta implementación."""
    logger.debug("No hay pool persistente que cerrar")


def check_connection() -> bool:
    """Verifica que la conexión a MySQL funcione. Útil para diagnósticos."""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
            return bool(row and row.get("ok") == 1)
    except pymysql.MySQLError as exc:
        logger.error("No se pudo conectar a MySQL: %s", exc)
        return False
