"""Marcadores no manuales y concordancia verbal direccional para LSC.

En LSC (y en todas las lenguas de señas) la **gramática no es solo
manual**. Una buena parte del significado vive en:

  · Marcadores no manuales (NMM): expresiones faciales y movimientos
    de cabeza/cuerpo que modifican o califican las señas. Por ejemplo:
       - cejas levantadas        → pregunta sí/no o tópico
       - cejas fruncidas         → pregunta WH (qué, dónde, cuándo)
       - movimiento horizontal   → negación
       - cabeza inclinada        → condicional o duda
  · Concordancia verbal espacial: ciertos verbos cambian su DIRECCIÓN
    física según el sujeto y el objeto. "Yo te doy" se signa moviendo
    la mano de mí hacia ti; "tú me das" hace lo opuesto. El infinitivo
    (DAR, AYUDAR, DECIR…) es el mismo, solo cambia la trayectoria.

Como nuestra app reproduce **clips aislados** (no podemos cambiar la
expresión facial del intérprete grabado, ni redirigir el movimiento de
la mano), aquí construimos **anotaciones visuales** que el frontend
superpone sobre cada seña. El usuario sordo (o el oyente que aprende)
ve QUÉ expresión facial debería acompañar la seña y EN QUÉ DIRECCIÓN
se haría el verbo.

Es una aproximación didáctica honesta — no reemplaza al intérprete
humano, pero le da al espectador la información gramatical que de otro
modo se perdería al usar clips estáticos.
"""
from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# Marcadores no manuales (NMM)
# ============================================================

# Cada marcador tiene un código corto (para CSS/iconos) y un label en
# español natural (para tooltip / aria-label).
@dataclass(frozen=True, slots=True)
class Marcador:
    codigo: str      # identificador estable (e.g. "cejas_arriba")
    label: str       # texto humano (e.g. "Cejas levantadas")
    icono: str       # emoji o símbolo para overlay (eslicero discreto)


CEJAS_ARRIBA   = Marcador("cejas_arriba",  "Cejas levantadas",   "↑")
CEJAS_FRUNCIDAS = Marcador("cejas_fruncidas", "Cejas fruncidas",  "︵")
CABEZA_NO      = Marcador("cabeza_no",      "Cabeza moviéndose lateral", "↔")
CABEZA_SI      = Marcador("cabeza_si",      "Cabeza asintiendo",  "↕")
TOPICO         = Marcador("topico",         "Tópico (cejas + pausa)", "◆")

_NULO = Marcador("", "", "")


# ============================================================
# Verbos direccionales
# ============================================================

# Verbos en LSC que requieren cambio de dirección espacial según
# sujeto y objeto. La lista coincide con verbos del diccionario LSC
# que tienen esta característica documentada.
VERBOS_DIRECCIONALES: frozenset[str] = frozenset({
    "dar", "decir", "hablar", "mandar", "enviar", "traer", "llevar",
    "mostrar", "ayudar", "invitar", "llamar", "preguntar", "responder",
    "explicar", "ensenar", "enseñar", "regalar", "prestar", "devolver",
    "mirar", "saludar",
})

# Pronombres tónicos y su "punto" en el espacio LSC.
# Usamos primera persona del singular como referencia (yo).
_PUNTOS_PRONOMBRE = {
    "yo":        "yo",
    "mi":        "yo",
    "mí":        "yo",
    "tu":        "tú",
    "tú":        "tú",
    "ti":        "tú",
    "usted":     "tú",
    "el":        "él/ella",
    "él":        "él/ella",
    "ella":      "él/ella",
    "nosotros":  "nosotros",
    "nosotras":  "nosotros",
    "ustedes":   "ustedes",
    "ellos":     "ellos",
    "ellas":     "ellos",
}


@dataclass(frozen=True, slots=True)
class Direccion:
    """Información direccional de un verbo espacial."""
    desde: str          # quien hace la acción (e.g. "yo")
    hacia: str          # quien la recibe (e.g. "tú")
    label: str          # texto humano para tooltip
    flecha: str         # representación textual visual (e.g. "yo → tú")


def punto_pronombre(palabra: str) -> str | None:
    """Mapea un pronombre español a su punto LSC. Devuelve None si no aplica."""
    if not palabra:
        return None
    return _PUNTOS_PRONOMBRE.get(palabra.strip().lower())


def es_verbo_direccional(lema: str) -> bool:
    return (lema or "").lower() in VERBOS_DIRECCIONALES


def construir_direccion(sujeto_lema: str | None, objeto_lema: str | None) -> Direccion | None:
    """Construye la `Direccion` si tenemos sujeto y objeto pronominales."""
    desde = punto_pronombre(sujeto_lema) if sujeto_lema else None
    hacia = punto_pronombre(objeto_lema) if objeto_lema else None
    if not (desde and hacia):
        return None
    if desde == hacia:
        return None
    return Direccion(
        desde=desde,
        hacia=hacia,
        label=f"Movimiento espacial: de {desde} hacia {hacia}",
        flecha=f"{desde} → {hacia}",
    )


# ============================================================
# Inferencia de dirección a partir de clíticos en el texto crudo
# ============================================================

# Patrones (sujeto, clítico) → (desde, hacia).
# Se evalúan sobre el texto original ANTES de filtrar funcionales,
# porque los clíticos (`me, te, le`) se descartan en la etapa A.
import re as _re

_PATRONES: tuple[tuple[_re.Pattern, str, str], ...] = (
    # Sujeto explícito + clítico
    (_re.compile(r"\byo\s+te\b",   _re.IGNORECASE), "yo", "tú"),
    (_re.compile(r"\byo\s+le\b",   _re.IGNORECASE), "yo", "él/ella"),
    (_re.compile(r"\byo\s+les\b",  _re.IGNORECASE), "yo", "ellos"),
    (_re.compile(r"\byo\s+os\b",   _re.IGNORECASE), "yo", "ustedes"),
    (_re.compile(r"\bt[úu]\s+me\b",  _re.IGNORECASE), "tú", "yo"),
    (_re.compile(r"\bt[úu]\s+nos\b", _re.IGNORECASE), "tú", "nosotros"),
    (_re.compile(r"\bt[úu]\s+le\b",  _re.IGNORECASE), "tú", "él/ella"),
    (_re.compile(r"\b[ée]l\s+me\b",   _re.IGNORECASE), "él/ella", "yo"),
    (_re.compile(r"\bella\s+me\b",    _re.IGNORECASE), "él/ella", "yo"),
    (_re.compile(r"\b[ée]l\s+te\b",   _re.IGNORECASE), "él/ella", "tú"),
    (_re.compile(r"\bella\s+te\b",    _re.IGNORECASE), "él/ella", "tú"),
    (_re.compile(r"\b[ée]l\s+nos\b",  _re.IGNORECASE), "él/ella", "nosotros"),
    (_re.compile(r"\bellos\s+me\b",   _re.IGNORECASE), "ellos", "yo"),
    (_re.compile(r"\bellas\s+me\b",   _re.IGNORECASE), "ellos", "yo"),
    (_re.compile(r"\bnosotros\s+te\b",_re.IGNORECASE), "nosotros", "tú"),
    (_re.compile(r"\bustedes\s+me\b", _re.IGNORECASE), "ustedes", "yo"),
    # Implícitos (sin sujeto explícito) — asumimos 1ª persona del singular
    # ("te ayudo" = "yo te ayudo")
    (_re.compile(r"(?<!\w)te\s+\w+", _re.IGNORECASE),  "yo", "tú"),
    (_re.compile(r"(?<!\w)les\s+\w+", _re.IGNORECASE), "yo", "ellos"),
)


def inferir_direccion_global(texto: str) -> Direccion | None:
    """Escanea el texto crudo buscando un patrón sujeto+clítico.

    Devuelve la `Direccion` del PRIMER patrón que matchee o None si no
    encuentra ninguno. Limitación consciente: no maneja oraciones con
    múltiples direcciones distintas; para eso habría que segmentar y
    correrlo por cláusula.
    """
    if not texto:
        return None
    for patron, desde, hacia in _PATRONES:
        if patron.search(texto):
            return Direccion(
                desde=desde,
                hacia=hacia,
                label=f"Movimiento espacial: de {desde} hacia {hacia}",
                flecha=f"{desde} → {hacia}",
            )
    return None
