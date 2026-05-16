"""Servicio de procesamiento de lenguaje natural para el traductor LSC.

Encapsula spaCy: tokeniza, lematiza, etiqueta POS, analiza dependencias y
expone toda esa información en `Token`s ricos que el orquestador usa para
construir la glosa LSC (filtrado funcional, reordenamiento TSOV, etc.).

Decisiones de diseño:
  · El parser sintáctico **está activado**: lo necesitamos para detectar el
    sujeto, objeto y núcleo verbal de cada oración (etapa F).
  · Conservamos la detección de frases multi-palabra (n-gramas) **antes**
    del análisis sintáctico — si algo aparece en la BD como `como_estas`,
    no queremos que el reordenador lo separe.
  · Las tablas de cierre (adverbios temporales, palabras WH, cópulas, etc.)
    son listas pequeñas de español neutro suficientes para el alcance
    académico del proyecto.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable, Sequence

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from config.settings import Config
from services.lematizador_verbos import lema_verbal
from services.sinonimos import canonicalizar as canonicalizar_sinonimo

logger = logging.getLogger(__name__)

# Placeholder para preservar la Ñ durante la normalización de acentos.
_ENE_PLACEHOLDER = "\x01"

# Longitud máxima de una frase multi-palabra a detectar (4 → 2 tokens).
_MAX_PHRASE_LEN = 4

# ---------- Tablas léxicas (cerradas) ----------

# Adverbios y locuciones temporales: van al inicio (etapa E).
ADVERBIOS_TEMPORALES = {
    "ayer", "hoy", "mañana", "ahora", "antes", "después", "despues",
    "anoche", "anteayer", "luego", "pronto", "temprano", "tarde",
    "después", "siempre", "nunca", "ya", "todavía", "todavia",
    "anteriormente", "previamente", "posteriormente",
}

# Palabras interrogativas (con y sin tilde por compatibilidad con
# textos sin acentos del usuario).
PALABRAS_WH = {
    "qué", "que", "quién", "quien", "quiénes", "quienes",
    "dónde", "donde", "cuándo", "cuando", "cómo", "como",
    "cuánto", "cuanto", "cuánta", "cuanta", "cuántos", "cuantos",
    "cuántas", "cuantas", "cuál", "cual", "cuáles", "cuales",
    "por_qué", "por_que",
}

# Pronombres átonos / clíticos: se omiten en LSC (la dirección los expresa).
PRONOMBRES_CLITICOS = {
    "me", "te", "se", "lo", "la", "los", "las", "le", "les", "nos", "os",
}

# Pronombres tónicos: SÍ se conservan (se signan).
PRONOMBRES_TONICOS = {
    "yo", "tú", "tu", "él", "el", "ella", "usted",
    "nosotros", "nosotras", "ustedes", "vosotros", "ellos", "ellas",
    "mí", "mi", "ti", "sí",
}

# Verbos cópula que se omiten cuando son enlace puro ("es alto" → ALTO).
VERBOS_COPULA = {"ser", "estar"}

# POS tags de spaCy a descartar siempre.
POS_DESCARTABLES = {"DET", "ADP", "PUNCT", "SYM", "X"}

# Lemas equivalentes a la negación.
LEMAS_NEGACION = {"no", "nada", "nunca", "tampoco", "jamás", "jamas", "ni"}


@dataclass(slots=True)
class Token:
    """Token enriquecido: cargamos toda la info que el orquestador necesita.

    `clave` es la forma normalizada para buscar en el diccionario.
    """

    texto: str           # forma superficial para mostrar al usuario
    clave: str           # clave normalizada (lema sin tildes, en minúsculas)
    pos: str = ""        # etiqueta POS spaCy (NOUN, VERB, ADJ, ...)
    dep: str = ""        # rol sintáctico (nsubj, obj, ROOT, ...)
    morph: str = ""      # morfología serializada (Tense, Number, ...)
    es_frase: bool = False
    sent_idx: int = 0    # índice de la oración a la que pertenece
    sent_start: bool = False  # ¿es el primer token de su oración?

    # Banderas que se completan en pipeline; permiten filtrar y reordenar
    # sin re-recorrer el árbol.
    es_funcional: bool = False
    es_negacion: bool = False
    es_wh: bool = False
    es_temporal: bool = False
    es_letra_explicita: bool = False  # parte de una secuencia de deletreo manual
    clausula_idx: int = 0             # índice de cláusula tras segmentación
    rol: str = "otro"    # tiempo|sujeto|objeto|verbo|negacion|wh|lugar|otro

    def as_dict(self) -> dict:
        return {
            "texto": self.texto,
            "clave": self.clave,
            "pos": self.pos,
            "dep": self.dep,
            "es_frase": self.es_frase,
            "rol": self.rol,
        }


# ---------- Helpers de normalización ----------

def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, conserva ñ."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = texto.replace("ñ", _ENE_PLACEHOLDER)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.replace(_ENE_PLACEHOLDER, "ñ")


def es_temporal(token: "Token") -> bool:
    """¿El token es un adverbio o expresión temporal?"""
    return token.clave in ADVERBIOS_TEMPORALES


def es_wh(token: "Token") -> bool:
    """¿El token es una palabra interrogativa real (qué, dónde, cómo, …)?

    Las claves se cruzan con `PALABRAS_WH` y se confirman por POS:
    aceptamos ADV, PRON, DET, INTJ, X. Descartamos SCONJ, VERB y AUX para
    no marcar como WH al "como" verbal de "yo como pan".
    """
    candidato = (
        token.clave in PALABRAS_WH or normalizar(token.texto) in PALABRAS_WH
    )
    if not candidato:
        return False
    return token.pos in {"ADV", "PRON", "DET", "INTJ", "X"}


def es_negacion(token: "Token") -> bool:
    return token.clave in LEMAS_NEGACION


def es_pronombre_clitico(texto_norm: str) -> bool:
    return texto_norm in PRONOMBRES_CLITICOS


def es_pronombre_tonico(texto_norm: str) -> bool:
    return texto_norm in PRONOMBRES_TONICOS


# ---------- Carga del modelo ----------

@lru_cache(maxsize=1)
def _load_spacy() -> Language:
    """Carga del modelo de español. Mantiene tagger + parser activos."""
    try:
        # 'ner' lo dejamos fuera (no lo usamos y ahorra tiempo).
        nlp = spacy.load(Config.SPACY_MODEL, disable=["ner"])
        logger.info(
            "Modelo spaCy '%s' cargado (parser %s, tagger %s)",
            Config.SPACY_MODEL,
            "ON" if "parser" in nlp.pipe_names else "OFF",
            "ON" if ("tagger" in nlp.pipe_names or "morphologizer" in nlp.pipe_names) else "OFF",
        )
        return nlp
    except OSError as exc:
        raise RuntimeError(
            f"El modelo spaCy '{Config.SPACY_MODEL}' no está instalado. "
            f"Ejecuta: python -m spacy download {Config.SPACY_MODEL}"
        ) from exc


# ============================================================
# Servicio
# ============================================================

class NLPService:
    """Procesa texto en español para producir Tokens listos para LSC."""

    def __init__(self, max_tokens: int | None = None) -> None:
        self.max_tokens = max_tokens or Config.MAX_TOKENS

    @property
    def nlp(self) -> Language:
        return _load_spacy()

    # ---------- API pública ----------

    def procesar(
        self,
        texto: str,
        frases_conocidas: Iterable[str] | None = None,
    ) -> list[Token]:
        """Tokeniza, etiqueta y agrupa frases multi-palabra.

        El resultado mantiene el orden natural del español; la reordenación
        TSOV la hace el `TraductorService` aguas abajo.
        """
        if not texto or not texto.strip():
            return []

        frases_set = set(frases_conocidas or ())
        doc: Doc = self.nlp(texto)

        # Aplanamos a tokens útiles (sin espacios ni puntuación pura).
        crudos = [t for t in doc if not t.is_space and t.text.strip()]
        crudos = crudos[: self.max_tokens]
        if not crudos:
            return []

        # Detección de frases (n-gramas) sobre formas y lemas normalizados.
        surfaces  = [normalizar(t.text)              for t in crudos]
        lemas     = [normalizar(t.lemma_ or t.text)  for t in crudos]

        # Identificamos cuál es el "primer token de contenido" de cada oración
        # (saltando puntuación inicial como ¿ ¡). Lo usamos para detectar
        # palabras al inicio que el tagger pequeño confunde con PROPN.
        primer_contenido_por_oracion: dict[int, int] = {}
        for idx, t in enumerate(crudos):
            if t.is_punct:
                continue
            sid = t.sent.start if t.sent else 0
            primer_contenido_por_oracion.setdefault(sid, idx)

        resultado: list[Token] = []
        i = 0
        n = len(crudos)
        while i < n:
            match = self._buscar_frase(surfaces, i, frases_set) or \
                    self._buscar_frase(lemas,    i, frases_set)
            if match is not None:
                largo, clave_frase = match
                texto_original = " ".join(crudos[k].text for k in range(i, i + largo))
                sid = crudos[i].sent.start if crudos[i].sent else 0
                resultado.append(Token(
                    texto=texto_original,
                    clave=clave_frase,
                    pos="X",                           # frase: tratada como atómica
                    dep="",
                    morph="",
                    es_frase=True,
                    sent_idx=sid,
                    sent_start=primer_contenido_por_oracion.get(sid) == i,
                ))
                i += largo
                continue

            spacy_tok = crudos[i]
            if spacy_tok.is_punct:
                i += 1
                continue

            sid = spacy_tok.sent.start if spacy_tok.sent else 0
            clave_inicial = lemas[i] or surfaces[i]
            # Si la forma superficial está en el mapping manual de verbos,
            # ese infinitivo gana sobre el lema (a veces incorrecto) de spaCy.
            # Cubre conjugaciones que el modelo md no resuelve (ej. comeré→comer).
            from_dict = lema_verbal(surfaces[i])
            if from_dict:
                clave_inicial = from_dict
            # Sinónimos afectivos / diminutivos → canónica (mamá→madre,
            # abuelita→abuela, hijito→hijo, ...). En LSC no existen
            # diminutivos morfológicos; la seña base cubre todas las variantes.
            # Probamos contra el lema y contra la forma superficial porque
            # spaCy a veces confunde 'mamá' con verbo y lo lematiza a 'mamar'.
            from_synonyms = (
                canonicalizar_sinonimo(clave_inicial)
                or canonicalizar_sinonimo(surfaces[i])
            )
            if from_synonyms:
                clave_inicial = from_synonyms
            tok = Token(
                texto=spacy_tok.text,
                clave=clave_inicial,
                pos=spacy_tok.pos_,
                dep=spacy_tok.dep_,
                morph=str(spacy_tok.morph) if spacy_tok.morph else "",
                es_frase=False,
                sent_idx=sid,
                sent_start=primer_contenido_por_oracion.get(sid) == i,
            )
            i += 1
            resultado.append(tok)

        return resultado

    def lemas_crudos(self, texto: str) -> list[str]:
        """Compatibilidad: solo devuelve la lista de claves."""
        return [t.clave for t in self.procesar(texto)]

    def dividir_para_deletreo(self, texto: str) -> list[str]:
        """Letras y dígitos limpios listos para dactilología."""
        normalizado = normalizar(texto)
        return [ch for ch in normalizado if re.match(r"[a-zñ0-9]", ch)]

    # ---------- Detectores que el TraductorService consume ----------

    @staticmethod
    def detectar_funcional(token: Token, claves_bd: set[str] | None = None) -> bool:
        """¿El token es palabra funcional que se descarta en LSC?

        Reglas aplicadas en orden:
          · `no`, palabras WH y adverbios temporales NUNCA se filtran aquí.
          · DET, ADP, PUNCT, SYM, X → SIEMPRE se filtran (no se rescatan
            aunque coincidan con una clave de la BD; un artículo "una" no
            se vuelve la seña de "uno" solo porque comparten lema).
          · Pronombres clíticos (me, te, se, lo, la, le, les) → siempre se
            filtran.
          · Para POS ambiguos (SCONJ, AUX cópula): si la clave aparece en
            `claves_bd`, se conserva — confiamos más en el diccionario que
            en el tagger. Esto cubre los típicos falsos positivos del
            modelo pequeño/medio ("como", "vives", "hola" → INTJ, etc.).
        """
        if token.es_negacion or token.es_wh or token.es_temporal:
            return False
        # Frases multi-palabra del diccionario: jamás se filtran.
        if token.es_frase:
            return False
        # Letras del alfabeto en un contexto de deletreo (ej. "a, b, c, d…")
        # nunca se filtran aunque "a" sea POS=ADP en español.
        if token.es_letra_explicita:
            return False
        # POS siempre descartables (no respetan BD por seguridad).
        if token.pos in POS_DESCARTABLES:
            return True
        # Pronombres clíticos: siempre fuera.
        if token.pos == "PRON" and es_pronombre_clitico(normalizar(token.texto)):
            return True
        # Para los siguientes POS dudosos confiamos en la BD si el lema existe.
        if claves_bd and token.clave in claves_bd:
            return False
        if token.pos == "SCONJ":
            return True
        if token.pos == "AUX" and token.clave in VERBOS_COPULA:
            return token.dep in {"cop", "ROOT", "aux"}
        return False

    # ---------- Remediación de POS al inicio de oración ----------

    def aplicar_sinonimos(self, tokens: list[Token]) -> list[Token]:
        """Garantiza que los sinónimos afectivos / coloquiales se apliquen.

        `procesar()` ya intenta canonicalizar, pero `remediar_inicio_oracion()`
        puede sobreescribir `token.clave` con el lema del re-tagging y borrar
        el sinónimo. Este paso final asegura que `mamá → madre`, `cicla →
        bicicleta`, etc., siempre tengan la última palabra.
        """
        for t in tokens:
            canon = (
                canonicalizar_sinonimo(t.clave)
                or canonicalizar_sinonimo(normalizar(t.texto))
            )
            if canon and canon != t.clave:
                t.clave = canon
        return tokens

    def remediar_inicio_oracion(self, tokens: list[Token]) -> list[Token]:
        """Re-procesa tokens al inicio de oración.

        El tagger del español tiene dos fallos típicos cuando una palabra
        aparece capitalizada al inicio de la oración:
          1. Un verbo conjugado se etiqueta como PROPN (`Comí`, `Iré`).
          2. Un verbo conjugado se etiqueta como VERB pero su lema sale
             incorrecto (`Iré` → lema `irar`, `comeré` → lema `comere`).

        Solución: a esos tokens los re-procesamos con un prefijo "yo "
        que da contexto al tagger, y nos quedamos con el lema/POS de la
        re-tokenización si el resultado es VERB.
        """
        for t in tokens:
            if not t.sent_start:
                continue
            if t.pos not in {"PROPN", "VERB"}:
                continue
            try:
                mini = self.nlp("yo " + t.texto.lower())
            except Exception:
                continue
            if len(mini) < 2:
                continue
            spt = mini[1]
            if spt.pos_ != "VERB":
                continue
            t.pos   = "VERB"
            t.clave = normalizar(spt.lemma_ or t.clave)
            t.morph = str(spt.morph) if spt.morph else ""
            if not t.dep:
                t.dep = "ROOT"
        return tokens

    @staticmethod
    def detectar_pregunta(texto_original: str, tokens: list[Token]) -> bool:
        """¿La oración es interrogativa?

        Confiamos solo en signos `¿` o `?`. Heurísticas tipo "comienza con
        WH-word" producen falsos positivos (ej. "Yo como pan" donde "como"
        puede leerse como WH si no se chequea POS).
        """
        t = (texto_original or "").strip()
        return "¿" in t or t.endswith("?")

    # ---------- Internos ----------

    @staticmethod
    def _buscar_frase(
        secuencia: Sequence[str], inicio: int, frases_conocidas: set[str]
    ) -> tuple[int, str] | None:
        if not frases_conocidas:
            return None
        max_n = min(_MAX_PHRASE_LEN, len(secuencia) - inicio)
        for n in range(max_n, 1, -1):
            candidato = "_".join(secuencia[inicio : inicio + n])
            if candidato in frases_conocidas:
                return n, candidato
        return None
