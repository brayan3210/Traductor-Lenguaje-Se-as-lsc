"""Inicialización de la base de datos MySQL para el traductor LSC.

Ejecuta el esquema y el seed a partir de los archivos SQL empaquetados.
Uso:
    python -m database.init_db              # crea BD + tablas + datos
    python -m database.init_db --schema     # solo tablas (vacías)
    python -m database.init_db --seed       # solo datos (asume esquema ya creado)

Se puede correr directamente o desde la línea de comandos de phpMyAdmin
importando los archivos SQL directamente.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pymysql

from config.settings import Config

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
SEED_PATH = Path(__file__).parent / "seed_data.sql"


def _split_statements(sql: str) -> list[str]:
    """Divide un script SQL por `;`, respetando líneas vacías y comentarios."""
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buffer).rstrip(";").strip())
            buffer = []
    if buffer:
        tail = "\n".join(buffer).strip()
        if tail:
            statements.append(tail)
    return [s for s in statements if s]


def _run_script(cursor, sql_text: str, label: str) -> int:
    statements = _split_statements(sql_text)
    for statement in statements:
        cursor.execute(statement)
    logger.info("[%s] %d sentencias ejecutadas", label, len(statements))
    return len(statements)


def _connect_without_db():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset=Config.DB_CHARSET,
    )


def _connect_to_db():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET,
    )


def apply_schema() -> None:
    """Crea la BD (si hace falta) y las tablas desde schema.sql."""
    sql_text = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = _connect_without_db()
    try:
        with conn.cursor() as cursor:
            _run_script(cursor, sql_text, label="schema")
        conn.commit()
    finally:
        conn.close()


def apply_seed() -> None:
    """Carga los datos iniciales desde seed_data.sql."""
    sql_text = SEED_PATH.read_text(encoding="utf-8")
    conn = _connect_to_db()
    try:
        with conn.cursor() as cursor:
            _run_script(cursor, sql_text, label="seed")
        conn.commit()
    finally:
        conn.close()


def verify() -> None:
    """Imprime un resumen por categoría para verificar la carga."""
    conn = _connect_to_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT categoria, COUNT(*) AS total "
                "FROM senas WHERE activo = 1 "
                "GROUP BY categoria ORDER BY categoria"
            )
            rows = cursor.fetchall()
            total = sum(row["total"] for row in rows)
            print("\n=== Diccionario cargado ===")
            for row in rows:
                print(f"  {row['categoria']:<12} {row['total']:>4}")
            print(f"  {'-' * 18}")
            print(f"  {'TOTAL':<12} {total:>4}\n")
    finally:
        conn.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    parser = argparse.ArgumentParser(description="Inicializa la BD del traductor LSC")
    parser.add_argument("--schema", action="store_true", help="Solo aplica el esquema")
    parser.add_argument("--seed", action="store_true", help="Solo aplica los datos")
    parser.add_argument("--verify", action="store_true", help="Solo verifica conteos")
    args = parser.parse_args()

    run_all = not (args.schema or args.seed or args.verify)

    try:
        if args.schema or run_all:
            logger.info("Aplicando esquema en %s...", Config.DB_NAME)
            apply_schema()
        if args.seed or run_all:
            logger.info("Cargando datos iniciales...")
            apply_seed()
        if args.verify or run_all:
            verify()
    except pymysql.MySQLError as exc:
        logger.error("Error MySQL: %s", exc)
        return 1

    logger.info("Inicialización completada correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
