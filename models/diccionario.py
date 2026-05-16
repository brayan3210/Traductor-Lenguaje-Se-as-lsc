"""Capa de acceso a datos para el diccionario de señas y el historial.

Expone dos repositorios:
    - DiccionarioRepository: consultas y mantenimiento del diccionario LSC.
    - HistorialRepository:   registro y lectura del historial de traducciones.

Todas las consultas utilizan parámetros ligados para evitar inyección SQL.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Sequence

from database.connection import get_cursor

logger = logging.getLogger(__name__)


class DiccionarioRepository:
    """Acceso a la tabla `senas`."""

    _BASE_SELECT = (
        "SELECT id, palabra, gif_url, tipo, categoria, descripcion, activo "
        "FROM senas"
    )

    # ---------- Lecturas ----------

    def listar(
        self,
        categoria: str | None = None,
        tipo: str | None = None,
        buscar: str | None = None,
        activos: bool = True,
    ) -> list[dict[str, Any]]:
        """Devuelve registros filtrados del diccionario."""
        clauses: list[str] = []
        params: list[Any] = []

        if activos:
            clauses.append("activo = %s")
            params.append(1)
        if categoria:
            clauses.append("categoria = %s")
            params.append(categoria)
        if tipo:
            clauses.append("tipo = %s")
            params.append(tipo)
        if buscar:
            clauses.append("palabra LIKE %s")
            params.append(f"%{buscar.lower()}%")

        query = self._BASE_SELECT
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY categoria, palabra"

        with get_cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())

    def obtener_por_palabra(self, palabra: str) -> dict[str, Any] | None:
        query = self._BASE_SELECT + " WHERE palabra = %s AND activo = 1 LIMIT 1"
        with get_cursor() as cursor:
            cursor.execute(query, (palabra,))
            return cursor.fetchone()

    def obtener_varias(self, palabras: Sequence[str]) -> dict[str, dict[str, Any]]:
        """Trae en una sola consulta todas las palabras pedidas.

        Devuelve un mapa palabra -> fila; las palabras no encontradas no aparecen.
        """
        if not palabras:
            return {}

        placeholders = ", ".join(["%s"] * len(palabras))
        query = (
            f"{self._BASE_SELECT} WHERE activo = 1 AND palabra IN ({placeholders})"
        )
        with get_cursor() as cursor:
            cursor.execute(query, tuple(palabras))
            rows = cursor.fetchall()
        return {row["palabra"]: row for row in rows}

    def listar_claves_de_frases(self) -> set[str]:
        """Retorna todas las palabras de tipo 'frase' (ej: me_llamo)."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT palabra FROM senas WHERE tipo = 'frase' AND activo = 1"
            )
            return {row["palabra"] for row in cursor.fetchall()}

    def contar_por_categoria(self) -> list[dict[str, Any]]:
        query = (
            "SELECT categoria, tipo, COUNT(*) AS total "
            "FROM senas WHERE activo = 1 "
            "GROUP BY categoria, tipo ORDER BY categoria"
        )
        with get_cursor() as cursor:
            cursor.execute(query)
            return list(cursor.fetchall())

    def estadisticas(self) -> dict[str, Any]:
        """Resumen agregado para la vista de estadísticas."""
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT tipo, COUNT(*) AS total FROM senas "
                "WHERE activo = 1 GROUP BY tipo"
            )
            por_tipo = {row["tipo"]: row["total"] for row in cursor.fetchall()}

            cursor.execute(
                "SELECT COUNT(*) AS total FROM senas WHERE activo = 1"
            )
            total_row = cursor.fetchone() or {}
            total = total_row.get("total", 0)

            cursor.execute(
                "SELECT COUNT(DISTINCT categoria) AS total FROM senas WHERE activo = 1"
            )
            cat_row = cursor.fetchone() or {}

        return {
            "total_senas": total,
            "total_categorias": cat_row.get("total", 0),
            "por_tipo": por_tipo,
        }

    def listar_categorias(self) -> list[str]:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT categoria FROM senas WHERE activo = 1 "
                "ORDER BY categoria"
            )
            return [row["categoria"] for row in cursor.fetchall()]

    # ---------- Escrituras (administración) ----------

    def crear(
        self,
        palabra: str,
        gif_url: str,
        tipo: str,
        categoria: str = "general",
        descripcion: str | None = None,
    ) -> int:
        query = (
            "INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(query, (palabra, gif_url, tipo, categoria, descripcion))
            return cursor.lastrowid

    def actualizar(self, sena_id: int, **campos: Any) -> bool:
        if not campos:
            return False
        permitidos = {"palabra", "gif_url", "tipo", "categoria", "descripcion", "activo"}
        asignaciones = []
        valores: list[Any] = []
        for clave, valor in campos.items():
            if clave not in permitidos:
                continue
            asignaciones.append(f"{clave} = %s")
            valores.append(valor)
        if not asignaciones:
            return False
        valores.append(sena_id)
        query = f"UPDATE senas SET {', '.join(asignaciones)} WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(query, valores)
            return cursor.rowcount > 0


class HistorialRepository:
    """Acceso a la tabla `historial`."""

    def registrar(
        self,
        texto_original: str,
        tokens: Iterable[str],
        total_senas: int,
        no_encontradas: int,
        ip_cliente: str | None = None,
    ) -> int:
        query = (
            "INSERT INTO historial "
            "(texto_original, tokens_json, total_senas, no_encontradas, ip_cliente) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        payload = json.dumps(list(tokens), ensure_ascii=False)
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                query,
                (texto_original, payload, total_senas, no_encontradas, ip_cliente),
            )
            return cursor.lastrowid

    def recientes(self, limite: int = 10) -> list[dict[str, Any]]:
        limite = max(1, min(int(limite), 100))
        query = (
            "SELECT id, texto_original, tokens_json, total_senas, "
            "no_encontradas, created_at "
            "FROM historial ORDER BY created_at DESC LIMIT %s"
        )
        with get_cursor() as cursor:
            cursor.execute(query, (limite,))
            rows = cursor.fetchall()
        for row in rows:
            try:
                row["tokens"] = json.loads(row.pop("tokens_json"))
            except (TypeError, ValueError):
                row["tokens"] = []
        return list(rows)

    def total(self) -> int:
        with get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM historial")
            row = cursor.fetchone() or {}
            return int(row.get("total", 0))
