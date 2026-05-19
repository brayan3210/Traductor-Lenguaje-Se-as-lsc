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

    # ---------- SUSTANTIVOS ↔ VERBOS ----------
    # En LSC el sustantivo y el verbo asociado comparten la misma seña.
    # Mapear el sustantivo al verbo permite que frases como
    # "Mi vida es mejor al estudio" o "gracias al estudio" resuelvan al
    # mismo video que "estudiar / estudié / estudio".
    "estudio":       "estudiar",
    "estudios":      "estudiar",
    "abrazo":        "abrazar",
    "abrazos":       "abrazar",
    "beso":          "besar",
    "besos":         "besar",
    "decision":      "decidir",
    "decisiones":    "decidir",
    "duda":          "dudar",
    "dudas":         "dudar",
    "olvido":        "olvidar",
    "olvidos":       "olvidar",
    "recuerdo":      "recordar",
    "recuerdos":     "recordar",
    "pensamiento":   "pensar",
    "pensamientos":  "pensar",
    "aprendizaje":   "aprender",
    "conocimiento":  "conocer",
    "conocimientos": "conocer",
    "comprension":   "entender",
    "defensa":       "defender",
    "preocupacion":  "preocupar",
    "preocupaciones":"preocupar",
    "interes":       "interesar",
    "intereses":     "interesar",
    "creencia":      "creer",
    "creencias":     "creer",

    # ---------- ADJETIVOS / EMOCIONES coloquiales ----------
    "gracioso":      "chistoso",
    "graciosa":      "chistoso",
    "divertido":     "chistoso",
    "divertida":     "chistoso",
    "liderazgo":     "lider",
    "pereza":        "perezoso",
    "vergüenza":     "pena",
    "verguenza":     "pena",  # tras normalizar()
    "felicidad":     "feliz",
    "alegria":       "feliz",
    "alegre":        "feliz",
    "tristeza":      "triste",
    "rabia":         "bravo",
    "ira":           "furioso",
    "enojo":         "bravo",
    "molesto":       "bravo",
    "asustado":      "miedo",
    "temor":         "miedo",
    "calmado":       "tranquilo",
    "calmada":       "tranquilo",

    # ---------- COMIDA: variantes regionales ----------
    "patata":        "papa_comida",
    "patatas":       "papa_comida",
    "torta":         "ponque",
    "pastel":        "ponque",
    "salchipapa":    "perro_caliente",  # aprox. sin seña propia
    "sandwich":      "sanduche",
    "sandwiches":    "sanduche",
    "emparedado":    "sanduche",
    "spaghetti":     "pasta",
    "espagueti":     "pasta",
    "macarrones":    "pasta",
    "platano":       "banano",
    "guineo":        "banano",

    # ---------- HOGAR ----------
    "shampoo":       "jabon",  # aprox: no hay seña propia de shampoo
    "champu":        "jabon",
    "papel":         "papel_higienico",
    "compresa":      "toalla_higienica",

    # ---------- DIRECCIONES ----------
    "encima":        "arriba",
    "debajo":        "abajo",
    "delante":       "adelante",
    "atras":         "detras",
    "dentro":        "adentro",
    "fuera":         "afuera",
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
