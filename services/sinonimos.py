"""Sinónimos afectivos / diminutivos → palabra canónica del diccionario LSC.

Cuando el usuario escribe formas familiares ("mamá", "abuelita", "hijito",
"padrecito", "papito"), queremos resolverlas a la seña canónica
("madre", "abuela", "hijo", "padre") en vez de marcarlas como NO_DISPONIBLE.

En LSC no existen diminutivos morfológicos como en español: la seña base
("MADRE") cubre todas las variantes afectivas (mamá, mami, mamita, …).
Por eso un único mapping es suficiente.

Aplicado en `nlp_service.procesar()` después del lema_verbal y antes de
construir el `Token`. Si la clave normalizada (o la forma superficial) está
en `_SINONIMOS`, se reemplaza por la canónica.
"""
from __future__ import annotations

# Forma normalizada (minúsculas, sin acentos, conserva ñ) → clave canónica.
# Las claves coinciden con las palabras del diccionario LSC.
_SINONIMOS: dict[str, str] = {
    # ---------- MADRE ----------
    "mama":       "madre",
    "mami":       "madre",
    "mamita":     "madre",
    "mamacita":   "madre",
    "mamasita":   "madre",
    "madrecita":  "madre",

    # ---------- PADRE ----------
    # 'papa' (sin tilde) coincide con 'patata', pero el diccionario LSC no
    # tiene seña de patata, así que mapear a 'padre' es seguro y cubre el
    # caso real: el usuario escribe 'papá' y normalize() le quita la tilde.
    "papa":       "padre",
    "papi":       "padre",
    "papito":     "padre",
    "papacito":   "padre",
    "papasito":   "padre",
    "padrecito":  "padre",

    # ---------- ABUELOS ----------
    "abuelita":   "abuela",
    "abuelitas":  "abuela",
    "abue":       "abuela",
    "abuelito":   "abuelo",
    "abuelitos":  "abuelo",

    # ---------- HIJOS ----------
    "hijito":     "hijo",
    "hijitos":    "hijo",
    "hijita":     "hija",
    "hijitas":    "hija",

    # ---------- HERMANOS ----------
    "hermanito":  "hermano",
    "hermanitos": "hermano",
    "hermanita":  "hermana",
    "hermanitas": "hermana",

    # ---------- NIÑOS ----------
    "niñito":     "niño",
    "niñitos":    "niño",
    "niñita":     "niña",
    "niñitas":    "niña",

    # ---------- AMIGOS ----------
    "amiguito":   "amigo",
    "amiguitos":  "amigo",
    "amiguita":   "amiga",
    "amiguitas":  "amiga",

    # ---------- BEBÉ ----------
    "bebito":     "bebe",
    "bebita":     "bebe",
    "bebesito":   "bebe",
    "bebesita":   "bebe",

    # ---------- TRANSPORTE coloquial ----------
    # Variantes informales que apuntan a la seña canónica de la BD.
    "cicla":      "bicicleta",
    "ciclas":     "bicicleta",
    "bici":       "bicicleta",
    "bicis":      "bicicleta",
    "auto":       "carro",
    "automovil":  "carro",
    "carrito":    "carro",
    "motico":     "moto",
    "motocicleta":"moto",
    "buseta":     "carro",   # sin seña propia; mapeo aproximado
    "avioncito":  "avion",
}


def canonicalizar(clave: str) -> str | None:
    """Devuelve la clave canónica si `clave` es una variante afectiva.

    Args:
        clave: la clave ya normalizada (minúsculas, sin acentos, ñ conservada).

    Returns:
        La clave canónica si está mapeada; `None` si no aplica.
    """
    if not clave:
        return None
    return _SINONIMOS.get(clave)
