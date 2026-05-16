"""Detector de frases largas con coincidencia tolerante a errores.

El matcher normal de n-gramas en `nlp_service.procesar()` solo mira hasta
4 tokens consecutivos (`_MAX_PHRASE_LEN`). Eso cubre frases cortas
como "buenos días" o "me llamo", pero no oraciones completas largas que
existen en el diccionario como referencia visual (ej. el video del edificio
de Bogotá).

Este módulo permite registrar oraciones completas con una lista de "stems
clave". Si el texto del usuario contiene al menos `min_keywords` de esos
stems —usando prefix-match para tolerar variantes y errores ortográficos
menores— se devuelve la clave canónica del diccionario para esa frase.

Uso:
    clave = detectar(texto_usuario)
    if clave:
        # texto_usuario describe la frase larga registrada
        ...
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from services.nlp_service import normalizar


@dataclass(frozen=True, slots=True)
class FraseLarga:
    """Una frase larga del diccionario y sus stems característicos."""
    clave_db: str
    stems: tuple[str, ...]      # prefijos a buscar en el texto normalizado
    min_keywords: int           # mínimo de stems distintos a encontrar
    glosa: str                  # glosa LSC final (mayúsculas, `·` entre cláusulas)


# ---------- Catálogo de frases largas ----------
#
# Cada entrada describe una frase del diccionario que excede 4 tokens.
# Los stems se comparan contra las palabras del texto del usuario tras
# `normalizar()` (minúsculas, sin acentos, conserva ñ). El match es por
# prefijo: el stem "edifici" detecta "edificio", "edificios", "edifico".
FRASES_LARGAS: tuple[FraseLarga, ...] = (
    FraseLarga(
        clave_db="edificio_ejemplo",
        stems=(
            "bogot",      # bogotá, bogota
            "edifici",    # edificio, edificios
            "centr",      # centro, centros
            "constru",    # construyendo, construyen, construir
            "grand",      # grande, grandísimo, grandes, grandote
            "alt",        # alto, altísimo
            "asombr",     # asombran, asombrado, asombro
            "person",     # personas, persona
        ),
        min_keywords=4,
        # Glosa LSC: tópico de lugar primero (BOGOTÁ CENTRO), luego objeto
        # con sus modificadores y verbo (EDIFICIO NUEVO GRANDE ALTO
        # CONSTRUIR), separados por `·` para marcar la pausa entre cláusulas.
        # La segunda cláusula es la reacción: PERSONA ASOMBRAR.
        glosa="BOGOTÁ CENTRO · EDIFICIO NUEVO GRANDE ALTO CONSTRUIR · PERSONA ASOMBRAR",
    ),
)


def detectar(texto: str) -> FraseLarga | None:
    """Devuelve la `FraseLarga` registrada si el texto coincide.

    Args:
        texto: el texto crudo del usuario.

    Returns:
        El objeto `FraseLarga` con `clave_db` y `glosa` listos para usar;
        `None` si no hay coincidencia suficiente.
    """
    if not texto:
        return None

    normalizado = normalizar(texto)
    palabras = re.findall(r"[a-zñ0-9]+", normalizado)
    if not palabras:
        return None

    for frase in FRASES_LARGAS:
        encontrados = 0
        for stem in frase.stems:
            if any(p.startswith(stem) for p in palabras):
                encontrados += 1
                if encontrados >= frase.min_keywords:
                    return frase
    return None
