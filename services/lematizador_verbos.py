"""Diccionario manual de conjugaciones verbales en español.

Razón de existir:
    El modelo `es_core_news_md` lematiza incorrectamente algunas formas
    verbales frecuentes (ej. `comeré → comere`, `comí → comí`, `digo → digo`).
    Este módulo provee un mapping `forma_conjugada → infinitivo` para los
    verbos del diccionario LSC + verbos comunes adicionales.

    El mapping se aplica en `nlp_service.procesar()` antes de buscar la
    palabra en la BD. La regla:
      · Si la forma normalizada está en `VERB_FORMS`, usar el infinitivo.
      · Las formas ambiguas (`como`, `vela`, `voto`, ...) se EXCLUYEN del
        dict para no romper la detección de WH ni de sustantivos.

Estructura:
    1. Verbos regulares: se generan por algoritmo a partir de la lista de
       infinitivos en `VERBOS_REGULARES`.
    2. Verbos irregulares: se declaran a mano en `VERBOS_IRREGULARES`.
    3. Formas explícitamente ambiguas: se eliminan en `_FORMAS_AMBIGUAS`.

El mapping resultante es un dict simple `{forma: infinitivo}` listo para
consulta O(1).
"""
from __future__ import annotations

# Verbos regulares de los que generamos paradigma completo a partir del
# infinitivo. Lista alineada con el diccionario LSC de Señas Co.
VERBOS_REGULARES: tuple[str, ...] = (
    # -ar
    "trabajar", "estudiar", "hablar", "escuchar", "llamar", "ayudar",
    "necesitar", "cantar", "correr",   # correr es -er; lo movemos abajo
    "caminar", "bailar", "cocinar", "mirar", "pensar", "jugar",
    # -er
    "beber", "ver", "comer", "leer",
    # -ir
    "vivir", "escribir", "sentir", "dormir",
)

# Conjugaciones de verbos irregulares y semi-irregulares de uso frecuente.
# Solo declaramos las formas que aparecen en español cotidiano y
# escogemos las menos ambiguas.
VERBOS_IRREGULARES: dict[str, str] = {
    # ser
    "soy": "ser", "eres": "ser", "es": "ser", "somos": "ser", "son": "ser",
    "fui": "ser", "fuiste": "ser", "fue": "ser", "fuimos": "ser", "fueron": "ser",
    "sere": "ser", "seras": "ser", "sera": "ser",
    "era": "ser", "eras": "ser", "eran": "ser",
    # estar
    "estoy": "estar", "estas": "estar", "esta": "estar",
    "estamos": "estar", "estan": "estar",
    "estuve": "estar", "estuviste": "estar", "estuvo": "estar",
    "estare": "estar", "estaras": "estar", "estara": "estar",
    "estaba": "estar", "estaban": "estar",
    # tener
    "tengo": "tener", "tienes": "tener", "tiene": "tener",
    "tenemos": "tener", "tienen": "tener",
    "tuve": "tener", "tuviste": "tener", "tuvo": "tener",
    "tuvimos": "tener", "tuvieron": "tener",
    "tendre": "tener", "tendras": "tener", "tendra": "tener",
    "tenia": "tener", "tenian": "tener",
    # querer
    "quiero": "querer", "quieres": "querer", "quiere": "querer",
    "queremos": "querer", "quieren": "querer",
    "quise": "querer", "quisiste": "querer", "quiso": "querer",
    "querre": "querer", "querras": "querer", "querra": "querer",
    "queria": "querer",
    # poder
    "puedo": "poder", "puedes": "poder", "puede": "poder",
    "podemos": "poder", "pueden": "poder",
    "pude": "poder", "pudiste": "poder", "pudo": "poder",
    "podre": "poder", "podra": "poder",
    # ir
    "voy": "ir", "vas": "ir", "va": "ir", "vamos": "ir", "van": "ir",
    "ire": "ir", "iras": "ir", "ira": "ir", "iremos": "ir", "iran": "ir",
    "iba": "ir", "iban": "ir",
    # dar (irregular muy frecuente; usado en LSC como verbo direccional)
    "doy": "dar", "das": "dar", "da": "dar", "damos": "dar", "dan": "dar",
    "di": "dar", "diste": "dar", "dio": "dar", "dimos": "dar", "dieron": "dar",
    "dare": "dar", "daras": "dar", "dara": "dar", "daremos": "dar", "daran": "dar",
    "daba": "dar", "dabas": "dar", "daban": "dar",
    # traer
    "traigo": "traer", "traes": "traer", "trae": "traer", "traemos": "traer", "traen": "traer",
    "traje": "traer", "trajiste": "traer", "trajo": "traer", "trajimos": "traer", "trajeron": "traer",
    # poner (relacionado con "dar/llevar" en muchos contextos)
    "pongo": "poner", "pones": "poner", "pone": "poner", "ponemos": "poner", "ponen": "poner",
    # hacer
    "hago": "hacer", "haces": "hacer", "hace": "hacer", "hacemos": "hacer", "hacen": "hacer",
    "hice": "hacer", "hizo": "hacer", "haran": "hacer", "haremos": "hacer",
    # venir
    "vengo": "venir", "vienes": "venir", "viene": "venir",
    "venimos": "venir", "vienen": "venir",
    "vine": "venir", "vino": "venir", "vinimos": "venir",
    # decir (no está en BD, pero es muy común)
    "digo": "hablar", "dices": "hablar", "dice": "hablar", "decimos": "hablar",
    "dicen": "hablar", "dije": "hablar", "dijo": "hablar",
    # saber
    "se": "saber",  # ojo: "sé" / "se"; se descarta más abajo si ambiguo
    "sabes": "saber", "sabe": "saber", "sabemos": "saber", "saben": "saber",
    "supe": "saber", "supo": "saber",
    # ver (irregular en pasado)
    "vi": "ver", "viste": "ver", "vio": "ver", "vimos": "ver", "vieron": "ver",
    # dormir
    "duermo": "dormir", "duermes": "dormir", "duerme": "dormir",
    "duermen": "dormir",
    # sentir
    "siento": "sentir", "sientes": "sentir", "siente": "sentir", "sienten": "sentir",
    # pensar
    "pienso": "pensar", "piensas": "pensar", "piensa": "pensar", "piensan": "pensar",
    # jugar
    "juego": "jugar", "juegas": "jugar", "juega": "jugar", "juegan": "jugar",
}

# Formas que coinciden con WH-words, pronombres, sustantivos o conectores
# y que por lo tanto NO debemos forzar a infinitivo verbal — la heurística
# del traductor decide en su lugar.
_FORMAS_AMBIGUAS: frozenset[str] = frozenset({
    "como",   # WH "cómo" / verbo "comer"
    "se",     # pronombre clítico / verbo "saber" / "ser"
    "vi",     # ya en irregulares; sin acento puede ser nombre propio
    "voy",    # solo verbo, no realmente ambiguo, pero lo dejamos por seguridad
    "te",     # pronombre clítico
    "le",     # pronombre clítico
    "vela",   # sustantivo común
    "voto",   # sustantivo común
    "puedo",  # ok no, esto no es ambiguo. dejarlo
})


def _expandir_regular(infinitivo: str) -> dict[str, str]:
    """Genera el paradigma básico de un verbo regular en -ar/-er/-ir."""
    if infinitivo.endswith("ar"):
        s = infinitivo[:-2]
        return {
            f"{s}o":     infinitivo,  # 1sg pres
            f"{s}as":    infinitivo,  # 2sg pres
            f"{s}a":     infinitivo,  # 3sg pres
            f"{s}amos":  infinitivo,  # 1pl pres
            f"{s}an":    infinitivo,  # 3pl pres
            f"{s}e":     infinitivo,  # 1sg pret (ej. "comí")  /ojo: "comió" 3sg
            f"{s}aste":  infinitivo,  # 2sg pret
            f"{s}aron":  infinitivo,  # 3pl pret
            f"{s}aba":   infinitivo,  # 1/3sg imp
            f"{s}abas":  infinitivo,  # 2sg imp
            f"{s}abamos": infinitivo, # 1pl imp
            f"{s}aban":  infinitivo,  # 3pl imp
            f"{s}are":   infinitivo,  # 1sg fut
            f"{s}aras":  infinitivo,  # 2sg fut
            f"{s}ara":   infinitivo,  # 3sg fut
            f"{s}aremos": infinitivo, # 1pl fut
            f"{s}aran":  infinitivo,  # 3pl fut
            # 1sg pret en -ar acentuado: "compré" → normalizado "compre"
            f"{s}e":     infinitivo,
        }
    if infinitivo.endswith("er"):
        s = infinitivo[:-2]
        return {
            f"{s}o":     infinitivo,
            f"{s}es":    infinitivo,
            f"{s}e":     infinitivo,
            f"{s}emos":  infinitivo,
            f"{s}en":    infinitivo,
            f"{s}i":     infinitivo,   # pret 1sg ("comí")
            f"{s}iste":  infinitivo,
            f"{s}io":    infinitivo,   # pret 3sg ("comió")
            f"{s}ieron": infinitivo,
            f"{s}ia":    infinitivo,   # imp ("comía")
            f"{s}ian":   infinitivo,
            f"{s}ere":   infinitivo,   # fut ("comeré")
            f"{s}eras":  infinitivo,
            f"{s}era":   infinitivo,
            f"{s}eremos": infinitivo,
            f"{s}eran":  infinitivo,
        }
    if infinitivo.endswith("ir"):
        s = infinitivo[:-2]
        return {
            f"{s}o":     infinitivo,
            f"{s}es":    infinitivo,
            f"{s}e":     infinitivo,
            f"{s}imos":  infinitivo,
            f"{s}en":    infinitivo,
            f"{s}i":     infinitivo,
            f"{s}iste":  infinitivo,
            f"{s}io":    infinitivo,
            f"{s}ieron": infinitivo,
            f"{s}ire":   infinitivo,
            f"{s}iras":  infinitivo,
            f"{s}ira":   infinitivo,
            f"{s}iremos": infinitivo,
            f"{s}iran":  infinitivo,
        }
    return {}


def _construir_dict() -> dict[str, str]:
    """Combina regulares e irregulares y descarta ambigüedades."""
    formas: dict[str, str] = {}
    for inf in VERBOS_REGULARES:
        formas.update(_expandir_regular(inf))
    formas.update(VERBOS_IRREGULARES)
    # Excluir las ambiguas
    for f in _FORMAS_AMBIGUAS:
        formas.pop(f, None)
    return formas


# Dict global, listo para consulta directa.
VERB_FORMS: dict[str, str] = _construir_dict()


def lema_verbal(forma_normalizada: str) -> str | None:
    """Devuelve el infinitivo si la forma está en el mapping, o None.

    `forma_normalizada` debe venir ya en minúsculas y sin tildes
    (ej. resultado de `nlp_service.normalizar(...)`).
    """
    return VERB_FORMS.get(forma_normalizada)
