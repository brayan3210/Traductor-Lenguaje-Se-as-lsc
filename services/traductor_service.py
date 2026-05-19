"""Servicio de traducción español → glosa LSC → secuencia de señas.

Pipeline (etapas A → F + búsqueda + B):

    1. NLP                — tokenización, lematización, POS, dependencias.
    2. Marcado            — anota negación, WH, temporal en cada token.
    3. Etapa A            — descarta palabras funcionales (artículos,
                            preposiciones, clíticos, cópulas).
    4. Etapa E            — extrae o infiere el marcador de TIEMPO.
    5. Etapa D            — separa palabras WH si la oración es interrogativa.
    6. Etapa C            — separa la negación.
    7. Etapa F            — reordena los tokens restantes a TSOV usando las
                            dependencias sintácticas.
    8. Composición        — `[T] + [LUGAR] + [SUJETO] + [OBJETO] + [VERBO]
                            + [NEG] + [WH]`.
    9. Búsqueda en BD     — una sola query por lote.
   10. Etapa B            — para los faltantes: deletreo SOLO si es PROPN o
                            sigla; en caso contrario, marca NO_DISPONIBLE.

El resultado expone:
    · `glosa`              — texto MAYÚSCULAS estilo glosado LSC.
    · `senas`              — secuencia ordenada lista para reproducir.
    · `es_pregunta`        — flag para activar el badge interrogativo en UI.
    · `tiene_negacion`     — flag para activar el badge de negación.
    · `palabras_no_disponibles` — palabras realmente sin seña ni dactilología.
    · `palabras_deletreadas`    — nombres propios / siglas deletreadas.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from models.diccionario import DiccionarioRepository, HistorialRepository
from services.frases_largas import detectar as detectar_frase_larga
from services.marcadores_lsc import (
    CABEZA_NO,
    CEJAS_ARRIBA,
    CEJAS_FRUNCIDAS,
    TOPICO,
    construir_direccion,
    es_verbo_direccional,
    inferir_direccion_global,
)
from services.media_resolver import resolver as resolver_media
from services.nlp_service import (
    NLPService,
    Token,
    es_negacion,
    es_temporal,
    es_wh,
    normalizar,
)

logger = logging.getLogger(__name__)


# Mapping dígito → palabra (fallback letra-a-letra para números sin seña propia).
NUMERO_A_PALABRA = {
    "0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
    "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve",
}

# Números con seña dedicada en el diccionario LSC. Si el usuario escribe
# "12", "100", "1000" preferimos esta seña a desglosar dígito por dígito.
# Las claves se buscan en BD; si una clave aún no tiene seña cargada el
# fallback dígito-a-dígito se aplica automáticamente.
NUMERO_DIRECTO = {
    "0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
    "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve",
    "10": "diez", "11": "once", "12": "doce", "13": "trece", "14": "catorce",
    "15": "quince", "16": "dieciseis", "17": "diecisiete",
    "18": "dieciocho", "19": "diecinueve",
    "50": "cincuenta", "100": "cien", "600": "seiscientos",
    "1000": "mil", "1000000": "millon",
}

# Separadores aceptados dentro de una secuencia numérica
# (ej. "12,1,2,3" o "12 1 2 3" o "12;1;2;3").
_SEP_NUMERO = re.compile(r"[\s,;.\-/|]+")

# Marcadores temporales insertados según el tiempo verbal.
TIEMPO_PASADO_DEFAULT = "antes"
TIEMPO_FUTURO_DEFAULT = "despues"

# Patrón conservador de sigla (2 a 5 letras, todas mayúsculas).
_SIGLA_RE = re.compile(r"^[A-ZÑ]{2,5}$")

# Conectores que delimitan cláusulas independientes para LSC.
# Cuando aparecen, partimos la oración en bloques que se procesan por
# separado y se concatenan con un marcador visual de pausa.
COORDINADORES = {"y", "e", "o", "u", "pero", "sino", "porque"}


@dataclass(slots=True)
class Sena:
    palabra: str
    gif_url: str           # URL real resuelta (puede ser .mp4 o .gif)
    tipo: str
    encontrado: bool
    fuente: str            # 'diccionario' | 'deletreo' | 'numero' | 'no_disponible'
    rol: str = "otro"
    media_type: str = "image"   # 'video' (.mp4 / .webm) | 'image' (.gif)
    clausula: int = 0           # índice de cláusula a la que pertenece (0,1,...)
    # Anotaciones gramaticales (marcador no manual + concordancia espacial)
    marcador_codigo: str = ""   # 'cejas_arriba' | 'cejas_fruncidas' | 'cabeza_no' | …
    marcador_label:  str = ""   # texto humano para tooltip / aria
    marcador_icono:  str = ""   # símbolo para overlay del player
    direccion:       str = ""   # 'yo → tú' (vacío si no es verbo direccional)
    direccion_label: str = ""   # tooltip explicativo

    def as_dict(self) -> dict[str, Any]:
        return {
            "palabra":         self.palabra,
            "gif_url":         self.gif_url,
            "tipo":            self.tipo,
            "encontrado":      self.encontrado,
            "fuente":          self.fuente,
            "rol":             self.rol,
            "media_type":      self.media_type,
            "clausula":        self.clausula,
            "marcador_codigo": self.marcador_codigo,
            "marcador_label":  self.marcador_label,
            "marcador_icono":  self.marcador_icono,
            "direccion":       self.direccion,
            "direccion_label": self.direccion_label,
        }


@dataclass(slots=True)
class ResultadoTraduccion:
    texto_original: str
    glosa: str
    tokens: list[str]
    senas: list[Sena]
    palabras_no_disponibles: list[str]
    palabras_deletreadas: list[str]
    es_pregunta: bool = False
    tiene_negacion: bool = False

    @property
    def total_senas(self) -> int:
        return len(self.senas)

    def as_dict(self) -> dict[str, Any]:
        return {
            "success":                  True,
            "texto_original":           self.texto_original,
            "glosa":                    self.glosa,
            "tokens":                   self.tokens,
            "senas":                    [s.as_dict() for s in self.senas],
            "total_senas":              self.total_senas,
            # Mantenemos `palabras_no_encontradas` por compatibilidad con la
            # UI antigua (frontend ya legacy sigue funcionando).
            "palabras_no_encontradas":  self.palabras_no_disponibles + self.palabras_deletreadas,
            "palabras_no_disponibles":  self.palabras_no_disponibles,
            "palabras_deletreadas":     self.palabras_deletreadas,
            "es_pregunta":              self.es_pregunta,
            "tiene_negacion":           self.tiene_negacion,
        }


# ============================================================
# Servicio principal
# ============================================================

class TraductorService:
    """Pipeline lingüístico + búsqueda en diccionario."""

    def __init__(
        self,
        nlp: NLPService | None = None,
        diccionario: DiccionarioRepository | None = None,
        historial: HistorialRepository | None = None,
    ) -> None:
        self.nlp = nlp or NLPService()
        self.diccionario = diccionario or DiccionarioRepository()
        self.historial = historial or HistorialRepository()

    # ---------- API pública ----------

    def traducir(
        self,
        texto: str,
        ip_cliente: str | None = None,
        guardar_historial: bool = True,
    ) -> ResultadoTraduccion:
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            return ResultadoTraduccion(
                texto_original="",
                glosa="",
                tokens=[],
                senas=[],
                palabras_no_disponibles=[],
                palabras_deletreadas=[],
            )

        # Caso especial: una sola letra del alfabeto.
        # Si el usuario escribe "a", "Ñ", "z", etc., la intención es ver la
        # seña dactilológica de esa letra. El pipeline normal trataría "a"
        # como preposición (POS=ADP) y la descartaría en la etapa A. Aquí
        # cortocircuitamos antes de tocar spaCy.
        sena_directa = self._buscar_letra_directa(texto_limpio)
        if sena_directa is not None:
            return ResultadoTraduccion(
                texto_original=texto_limpio,
                glosa=sena_directa.palabra.upper(),
                tokens=[sena_directa.palabra],
                senas=[sena_directa],
                palabras_no_disponibles=[],
                palabras_deletreadas=[],
            )

        # Caso especial: frase larga registrada (excede _MAX_PHRASE_LEN).
        # Si el texto contiene los keywords característicos de una frase
        # del diccionario (ej. la oración del edificio en el centro de
        # Bogotá), corto el pipeline y devuelvo directamente esa Sena.
        # Tolera variaciones ortográficas (prefix match sin acentos).
        frase_larga = detectar_frase_larga(texto_limpio)
        if frase_larga:
            entrada_frase = self.diccionario.obtener_por_palabra(frase_larga.clave_db)
            if entrada_frase:
                sena_frase = self._sena_desde_registro(entrada_frase, rol="otro")
                return ResultadoTraduccion(
                    texto_original=texto_limpio,
                    glosa=frase_larga.glosa,
                    tokens=[sena_frase.palabra],
                    senas=[sena_frase],
                    palabras_no_disponibles=[],
                    palabras_deletreadas=[],
                )

        # 1) NLP
        frases_conocidas = self.diccionario.listar_claves_de_frases()
        tokens = self.nlp.procesar(texto_limpio, frases_conocidas=frases_conocidas)
        if not tokens:
            return ResultadoTraduccion(
                texto_original=texto_limpio, glosa="",
                tokens=[], senas=[],
                palabras_no_disponibles=[], palabras_deletreadas=[],
            )

        # 1.b) Remediación de tokens al inicio (verbos mal etiquetados)
        tokens = self.nlp.remediar_inicio_oracion(tokens)

        # 1.c) Sinónimos afectivos / coloquiales (mamá→madre, cicla→bicicleta).
        # Se aplica DESPUÉS de remediar porque la remediación puede haber
        # sobreescrito la clave con un re-lema (ej. mamá → mamar).
        tokens = self.nlp.aplicar_sinonimos(tokens)

        # 2) Marcado
        for t in tokens:
            t.es_negacion = es_negacion(t)
            t.es_wh       = es_wh(t)
            t.es_temporal = es_temporal(t)

        # 2.b) Detección de secuencias de deletreo: "a, b, c, …" o "a b c d".
        # Si hay 2+ tokens de una sola letra, los marcamos para que el
        # filtro funcional (etapa A) no descarte la "a" como preposición.
        self._marcar_letras_explicitas(tokens)

        es_pregunta = self.nlp.detectar_pregunta(texto_limpio, tokens)

        # Cache de claves disponibles en BD para no descartar contenido que
        # SÍ se puede signar (cubre falsos positivos del POS tagger).
        claves_bd = self._claves_diccionario()

        # 3) Etapa A — filtrar funcionales
        for t in tokens:
            t.es_funcional = self.nlp.detectar_funcional(t, claves_bd=claves_bd)
        tokens = [t for t in tokens if not t.es_funcional]

        # 4) Etapa E — marcador temporal (global a la oración entera)
        marcador_tiempo, tokens = self._extraer_marcador_temporal(tokens, claves_bd=claves_bd)

        # 5) Etapa D — palabras WH (solo si la oración es pregunta)
        wh_tokens: list[Token] = []
        if es_pregunta:
            wh_tokens = [t for t in tokens if t.es_wh]
            tokens = [t for t in tokens if not t.es_wh]

        # 6) Segmentación por cláusulas (NUEVO)
        # Partimos la lista de tokens cada vez que aparece un coordinador
        # (y, pero, o, porque). Cada cláusula se procesa independientemente
        # con etapas C (negación) y F (TSOV) y se concatenan con un
        # marcador visual de pausa entre ellas.
        clausulas = self._segmentar_clausulas(tokens)

        # 7) Procesar cada cláusula: negación + TSOV
        clausulas_procesadas: list[list[Token]] = []
        tiene_negacion = False
        for clausula in clausulas:
            neg = [t for t in clausula if t.es_negacion]
            sin_neg = [t for t in clausula if not t.es_negacion]
            ordenados = self._reordenar_tsov(sin_neg)
            ordenados.extend(neg)            # negación al final de cada cláusula
            if neg:
                tiene_negacion = True
            clausulas_procesadas.append(ordenados)

        # 8) Composición final
        # Estructura LSC: [tiempo] + clausula_1 + ... + clausula_n + [WH global]
        glosa_tokens: list[Token] = []
        if marcador_tiempo:
            glosa_tokens.append(marcador_tiempo)
        for idx, clausula in enumerate(clausulas_procesadas):
            for t in clausula:
                t.clausula_idx = idx + (1 if marcador_tiempo else 0)
            glosa_tokens.extend(clausula)
        # Las WH-tokens van al final de la última cláusula
        if wh_tokens:
            ultimo_idx = (len(clausulas_procesadas) - 1) + (1 if marcador_tiempo else 0)
            for t in wh_tokens:
                t.clausula_idx = max(ultimo_idx, 0)
            glosa_tokens.extend(wh_tokens)
        if marcador_tiempo:
            marcador_tiempo.clausula_idx = 0

        # 9) Búsqueda en diccionario (lote)
        claves_unicas = list({t.clave for t in glosa_tokens if t.clave})
        diccionario = self.diccionario.obtener_varias(claves_unicas)

        # 10) Etapa B — resolución conservadora
        senas, no_disponibles, deletreadas = self._resolver_senas(glosa_tokens, diccionario)

        # 10.b) Anotaciones gramaticales: marcadores no manuales y dirección
        # espacial de los verbos. NO afecta la secuencia ni la glosa, solo
        # adjunta info para que el frontend la renderice como overlay.
        self._anotar_marcadores(senas, glosa_tokens, es_pregunta, tiene_negacion, texto_limpio)

        # Glosa con separador `·` entre cláusulas para reflejar la pausa LSC.
        glosa_str = self._construir_glosa_string(glosa_tokens)

        resultado = ResultadoTraduccion(
            texto_original=texto_limpio,
            glosa=glosa_str,
            tokens=[t.clave for t in glosa_tokens],
            senas=senas,
            palabras_no_disponibles=no_disponibles,
            palabras_deletreadas=deletreadas,
            es_pregunta=es_pregunta,
            tiene_negacion=tiene_negacion,
        )

        if guardar_historial:
            try:
                self.historial.registrar(
                    texto_original=texto_limpio,
                    tokens=resultado.tokens,
                    total_senas=resultado.total_senas,
                    no_encontradas=len(no_disponibles) + len(deletreadas),
                    ip_cliente=ip_cliente,
                )
            except Exception:
                logger.exception("No se pudo registrar el historial")

        return resultado

    # ============================================================
    # ETAPA E — marcador temporal
    # ============================================================

    def _extraer_marcador_temporal(
        self, tokens: list[Token], claves_bd: set[str] | None = None
    ) -> tuple[Token | None, list[Token]]:
        """Si hay adverbio temporal explícito, lo saca y lo devuelve.
        Si no, mira el tiempo verbal del verbo raíz e infiere ANTES/DESPUÉS.
        Devuelve (marcador, tokens_sin_temporal).
        """
        # Caso 1: adverbio temporal explícito.
        explicitos = [t for t in tokens if t.es_temporal]
        if explicitos:
            primero = explicitos[0]
            primero.rol = "tiempo"
            tokens_restantes = [t for t in tokens if t is not primero]
            tokens_restantes = [t for t in tokens_restantes if not t.es_temporal]
            return primero, tokens_restantes

        # Caso 2: inferir por tiempo verbal del ROOT.
        # Solo insertamos un marcador si el verbo principal SÍ se va a
        # signar — si su lema no está en la BD, agregar "antes/despues"
        # solo agrega ruido al resultado.
        verbo = self._localizar_verbo_principal(tokens)
        if not verbo:
            return None, tokens
        if claves_bd is not None and verbo.clave not in claves_bd:
            return None, tokens

        morph = verbo.morph or ""
        if "Tense=Past" in morph or "VerbForm=Part" in morph:
            marcador = TIEMPO_PASADO_DEFAULT
        elif "Tense=Fut" in morph:
            marcador = TIEMPO_FUTURO_DEFAULT
        else:
            return None, tokens

        # Solo insertamos el marcador si la palabra está en el diccionario.
        if claves_bd is not None and marcador not in claves_bd:
            return None, tokens
        return self._token_temporal(marcador), tokens

    @staticmethod
    def _token_temporal(clave: str) -> Token:
        return Token(
            texto=clave,
            clave=clave,
            pos="ADV",
            dep="advmod",
            es_temporal=True,
            rol="tiempo",
        )

    # ============================================================
    # ETAPA F — reordenamiento TSOV
    # ============================================================

    def _reordenar_tsov(self, tokens: list[Token]) -> list[Token]:
        """Reordena `tokens` (sin tiempo, sin negación, sin WH) a TSOV.

        Heurística:
          · agrupa los tokens por la oración a la que pertenecen.
          · dentro de cada oración usa las dependencias para asignar rol:
              nsubj / nsubj:pass    → SUJETO
              obj / dobj / iobj     → OBJETO
              ROOT (verbo)          → VERBO
              obl con preposiciones de lugar → LUGAR
              cualquier otro        → ADJUNTO (mantiene orden relativo)
          · concatena: LUGAR + SUJETO + OBJETO + ADJUNTOS + VERBO.
        """
        if not tokens:
            return []

        salida: list[Token] = []
        # Agrupar por oración para no mezclar slots entre oraciones.
        oraciones: dict[int, list[Token]] = {}
        for t in tokens:
            oraciones.setdefault(t.sent_idx, []).append(t)

        for _, oracion in oraciones.items():
            sujeto:    list[Token] = []
            objeto:    list[Token] = []
            verbo:     list[Token] = []
            lugar:     list[Token] = []
            adjuntos:  list[Token] = []

            for t in oracion:
                rol = self._asignar_rol(t)
                t.rol = rol
                if   rol == "sujeto":  sujeto.append(t)
                elif rol == "objeto":  objeto.append(t)
                elif rol == "verbo":   verbo.append(t)
                elif rol == "lugar":   lugar.append(t)
                else:                  adjuntos.append(t)

            salida.extend(lugar)
            salida.extend(sujeto)
            salida.extend(objeto)
            salida.extend(adjuntos)
            salida.extend(verbo)

        return salida

    @staticmethod
    def _asignar_rol(token: Token) -> str:
        # Letras explícitas (deletreo manual) preservan su orden natural —
        # nunca se les asigna un slot semántico.
        if token.es_letra_explicita:
            return "otro"

        dep = token.dep or ""
        pos = token.pos or ""

        if dep in {"nsubj", "nsubj:pass"} or (pos == "PRON" and dep != "obj"):
            return "sujeto"
        if dep in {"obj", "dobj", "iobj"}:
            return "objeto"
        if dep == "ROOT" and pos in {"VERB", "AUX"}:
            return "verbo"
        if dep == "obl":
            # Heurística simple: lo tratamos como LUGAR si es sustantivo;
            # si no, queda como adjunto.
            return "lugar" if pos in {"NOUN", "PROPN"} else "otro"
        if pos == "VERB":
            return "verbo"
        return "otro"

    @staticmethod
    def _localizar_verbo_principal(tokens: list[Token]) -> Token | None:
        for t in tokens:
            if t.dep == "ROOT" and t.pos in {"VERB", "AUX"}:
                return t
        for t in tokens:
            if t.pos == "VERB":
                return t
        return None

    # ============================================================
    # ETAPA B — búsqueda + resolución conservadora
    # ============================================================

    def _resolver_senas(
        self,
        tokens: list[Token],
        diccionario: dict[str, dict[str, Any]],
    ) -> tuple[list[Sena], list[str], list[str]]:
        senas: list[Sena] = []
        no_disponibles: list[str] = []
        deletreadas: list[str] = []

        for token in tokens:
            cl = token.clausula_idx
            entrada = diccionario.get(token.clave)
            # Fallback: si el lema no está en BD, prueba la forma superficial
            # normalizada. Cubre fallos del lematizador como "adios → adio".
            if not entrada:
                surface = normalizar(token.texto)
                if surface and surface != token.clave:
                    entrada = self._buscar_en_bd(surface)
                    if entrada:
                        token.clave = surface
            if entrada:
                senas.append(self._sena_desde_registro(entrada, rol=token.rol, clausula=cl))
                continue

            # 1) Dígitos puros: convertir a palabras-número.
            senas_numero = self._traducir_numero(token.texto, rol=token.rol, clausula=cl)
            if senas_numero:
                senas.extend(senas_numero)
                continue

            # 2) Etapa B: solo deletrear si es PROPN o sigla.
            if self._debe_deletrearse(token):
                letras = self._deletrear(token.texto, rol=token.rol, clausula=cl)
                if letras:
                    senas.extend(letras)
                    deletreadas.append(token.texto)
                    continue

            # 3) En cualquier otro caso: marca como no disponible.
            senas.append(Sena(
                palabra=token.texto,
                gif_url="",
                tipo="desconocido",
                encontrado=False,
                fuente="no_disponible",
                rol=token.rol,
                clausula=cl,
            ))
            no_disponibles.append(token.texto)

        return senas, no_disponibles, deletreadas

    @staticmethod
    def _debe_deletrearse(token: Token) -> bool:
        """¿Esta palabra cumple los criterios estrictos para dactilología?

        Reglas:
          · Sigla (2-5 letras todas en mayúsculas) → SÍ deletrear.
          · PROPN → SÍ deletrear (la remediación ya corrigió la mayoría de
            los falsos positivos PROPN-en-realidad-VERB al inicio de
            oración, así que aquí confiamos en la etiqueta).
        """
        if _SIGLA_RE.match(token.texto):
            return True
        return token.pos == "PROPN"

    # ---------- Marcadores no manuales y direccionalidad ----------

    def _anotar_marcadores(
        self,
        senas: list[Sena],
        tokens: list[Token],
        es_pregunta: bool,
        tiene_negacion: bool,
        texto_original: str = "",
    ) -> None:
        """Adjunta a cada `Sena` info gramatical visualizable.

        Reglas aplicadas (priorizadas: la última gana si hay conflicto):
          1. Si la oración es pregunta sí/no (sin WH explícita) → marca
             todas las señas con `cejas_arriba`.
          2. Si la oración es pregunta WH → marca la(s) seña(s) WH con
             `cejas_fruncidas` y las demás con `cejas_arriba` (intensidad
             menor pero la pregunta sigue activa).
          3. Si hay negación → marca la(s) seña(s) de rol `otro` con
             clave `no/nada/nunca/...` con `cabeza_no`.
          4. Topicalización: la primera seña de la primera cláusula con
             rol "sujeto" o "objeto" recibe `topico` (cejas + pausa).
          5. Verbos direccionales: si el verbo está en `VERBOS_DIRECCIONALES`
             y hay sujeto + objeto pronominales en la cláusula, se calcula
             la flecha (ej. "yo → tú").
        """
        if not senas:
            return

        # Mapeo Sena → token original (mismo índice porque _resolver_senas
        # mantiene el orden 1:1 cuando la entrada está en BD; los casos de
        # deletreo/numero/no_disponible expanden y no preservan la relación
        # — los detectamos por fuente).
        # Para esta capa de anotación trabajamos directamente sobre Senas
        # y consultamos los tokens cuando hace falta.
        wh_claves = {"que", "quien", "donde", "cuando", "como", "cuanto", "por_que"}
        neg_claves = {"no", "nada", "nunca", "tampoco", "jamas", "ni"}

        # 1 + 2: marcadores de pregunta
        tiene_wh_explicita = any(s.palabra in wh_claves for s in senas)
        if es_pregunta:
            for s in senas:
                if s.palabra in wh_claves:
                    s.marcador_codigo = CEJAS_FRUNCIDAS.codigo
                    s.marcador_label  = CEJAS_FRUNCIDAS.label
                    s.marcador_icono  = CEJAS_FRUNCIDAS.icono
                else:
                    s.marcador_codigo = CEJAS_ARRIBA.codigo
                    s.marcador_label  = CEJAS_ARRIBA.label
                    s.marcador_icono  = CEJAS_ARRIBA.icono
            # Si NO hay WH (es sí/no), todas con cejas_arriba ya quedó.

        # 3: negación
        if tiene_negacion:
            for s in senas:
                if s.palabra in neg_claves:
                    s.marcador_codigo = CABEZA_NO.codigo
                    s.marcador_label  = CABEZA_NO.label
                    s.marcador_icono  = CABEZA_NO.icono

        # 4: topicalización del primer elemento de la primera cláusula
        # (sujeto u objeto), si hay más de una palabra y no es una pregunta
        # ni una glosa de un solo elemento.
        if len(senas) >= 3 and not es_pregunta:
            primera = senas[0]
            if primera.rol in {"sujeto", "objeto", "lugar"} and not primera.marcador_codigo:
                primera.marcador_codigo = TOPICO.codigo
                primera.marcador_label  = TOPICO.label
                primera.marcador_icono  = TOPICO.icono

        # 5: verbos direccionales — primero intentamos por cláusula con
        # roles explícitos; si no, escaneamos el texto crudo buscando
        # patrones de clíticos ("yo te ayudo", "tú me das").
        self._anotar_direccionales(senas, texto_original)

    @staticmethod
    def _anotar_direccionales(senas: list[Sena], texto_original: str = "") -> None:
        """Marca cada verbo direccional con su flecha espacial.

        Cascada:
          1. Si en la cláusula del verbo hay sujeto + objeto pronominales
             explícitos, los usa.
          2. Si no, recurre a un escaneo regex del texto original que
             reconoce patrones como "yo te ayudo", "tú me das", etc.
             (los clíticos `me/te/le` se filtran en la etapa A, por eso
             necesitamos el texto crudo).

        Para detectar si el verbo es direccional usamos la forma canónica
        (lema). Esto cubre el caso en que la palabra apareció como `no
        disponible` y la sena conserva la forma conjugada original.
        """
        from services.lematizador_verbos import lema_verbal

        def _es_verbo_direccional_de_sena(s: Sena) -> bool:
            if es_verbo_direccional(s.palabra):
                return True
            # Si la sena viene con forma conjugada (caso no_disponible),
            # intenta lematizar antes de descartar.
            forma = (s.palabra or "").lower()
            lema = lema_verbal(forma)
            return bool(lema and es_verbo_direccional(lema))

        # Agrupamos índices por cláusula
        por_clausula: dict[int, list[int]] = {}
        for i, s in enumerate(senas):
            por_clausula.setdefault(s.clausula, []).append(i)

        # Para fallback por texto, calculamos UNA vez la dirección global.
        direccion_global = inferir_direccion_global(texto_original)

        for indices in por_clausula.values():
            sujeto_lema: str | None = None
            objeto_lema: str | None = None
            verbo_idx: int | None = None
            for i in indices:
                s = senas[i]
                if s.rol == "sujeto" and not sujeto_lema:
                    sujeto_lema = s.palabra
                elif s.rol == "objeto" and not objeto_lema:
                    objeto_lema = s.palabra
                elif s.rol == "verbo" and verbo_idx is None and _es_verbo_direccional_de_sena(s):
                    verbo_idx = i

            if verbo_idx is None:
                continue

            # Intento 1: pronombres explícitos sujeto+objeto
            direccion = construir_direccion(sujeto_lema, objeto_lema)
            # Intento 2: fallback global por clíticos en el texto crudo
            if direccion is None and direccion_global is not None:
                direccion = direccion_global
            if direccion is None:
                continue
            senas[verbo_idx].direccion       = direccion.flecha
            senas[verbo_idx].direccion_label = direccion.label

    # ---------- Construcción de la glosa ----------

    @staticmethod
    def _construir_glosa_string(tokens: list[Token]) -> str:
        """Concatena los tokens en una glosa MAYÚSCULAS, insertando `·`
        cuando el índice de cláusula cambia (visualiza la pausa LSC).
        """
        partes: list[str] = []
        last_cl: int | None = None
        for t in tokens:
            if not t.clave:
                continue
            if last_cl is not None and t.clausula_idx != last_cl:
                partes.append("·")
            partes.append(t.clave.replace("_", " ").upper())
            last_cl = t.clausula_idx
        return " ".join(partes)

    # ---------- Segmentación de cláusulas ----------

    def _segmentar_clausulas(self, tokens: list[Token]) -> list[list[Token]]:
        """Divide la lista de tokens en cláusulas separadas por coordinadores.

        Una cláusula es un bloque entre conectores como `y, pero, o, porque`.
        El conector mismo se descarta (en LSC normalmente se omite y el
        cambio de cláusula se marca con pausa o expresión facial).

        Si no hay coordinadores, devuelve `[tokens]` (una sola cláusula).
        """
        if not tokens:
            return []
        clausulas: list[list[Token]] = [[]]
        for t in tokens:
            if t.clave in COORDINADORES and t.pos in {"CCONJ", "SCONJ"}:
                if clausulas[-1]:
                    clausulas.append([])
                continue
            clausulas[-1].append(t)
        return [c for c in clausulas if c]

    # ---------- Casos especiales: letras explícitas ----------

    @staticmethod
    def _es_letra_alfabeto(texto: str) -> bool:
        s = (texto or "").strip().lower()
        return len(s) == 1 and (s.isalpha() or s == "ñ")

    def _marcar_letras_explicitas(self, tokens: list[Token]) -> None:
        """Marca como `es_letra_explicita=True` los tokens de una sola letra
        cuando hay al menos dos en la oración. Cubre patrones de deletreo
        explícito como `"a, b, c, d, e"` o `"a b c"` que el usuario escribe
        para visualizar varias señas dactilológicas a la vez.
        """
        candidatos = [t for t in tokens if self._es_letra_alfabeto(t.texto)]
        if len(candidatos) >= 2:
            for t in candidatos:
                t.es_letra_explicita = True

    def _buscar_letra_directa(self, texto: str) -> Sena | None:
        """Si el texto es exactamente una letra del alfabeto, devuelve su
        Sena (con el media resuelto). En cualquier otro caso devuelve None
        y el flujo continúa con el pipeline normal.
        """
        surf = normalizar(texto.strip())
        if len(surf) != 1:
            return None
        if not (surf.isalpha() or surf == "ñ"):
            return None
        entrada = self.diccionario.obtener_varias([surf]).get(surf)
        if not entrada:
            return None
        return self._sena_desde_registro(entrada, rol="otro")

    # ---------- Acceso a BD ----------

    def _buscar_en_bd(self, palabra: str) -> dict[str, Any] | None:
        """Lookup individual a la BD (fallback cuando el batch falla)."""
        try:
            return self.diccionario.obtener_por_palabra(palabra)
        except Exception:
            return None

    # ---------- Cache de claves del diccionario ----------

    def _claves_diccionario(self) -> set[str]:
        """Devuelve TODAS las claves del diccionario para no descartar palabras
        que SÍ tienen seña por culpa de un mal POS tag."""
        try:
            entradas = self.diccionario.listar()
            return {e["palabra"] for e in entradas}
        except Exception:
            logger.exception("No se pudo construir cache de claves del diccionario")
            return set()

    # ---------- Conversión de registros ----------

    @staticmethod
    def _sena_desde_registro(registro: dict[str, Any], rol: str = "otro", clausula: int = 0) -> Sena:
        media = resolver_media(registro["gif_url"])
        return Sena(
            palabra=registro["palabra"],
            gif_url=media.url,
            tipo=registro["tipo"],
            encontrado=True,                 # existe en BD; el archivo en disco
            fuente="diccionario",            # lo verifica el frontend con un onerror.
            rol=rol,
            media_type=media.media_type,
            clausula=clausula,
        )

    def _traducir_numero(self, texto: str, rol: str = "otro", clausula: int = 0) -> list[Sena]:
        """Traduce un token numérico a su(s) seña(s).

        Acepta:
          - Un único número entero ("12", "100", "1000").
          - Una secuencia separada por comas/espacios/punto/punto-y-coma/
            guion/barra ("12,1,2,3" o "12 1 2 3" o "12;1;2").
          - Cualquier mezcla; los separadores se descartan.

        Estrategia por número:
          1. Si está en NUMERO_DIRECTO **y existe en BD** → una sola seña
             (ej. 12 → DOCE, 100 → CIEN, 1000 → MIL).
          2. Si no, fallback dígito a dígito (ej. 73 → SIETE TRES).
        """
        # Limpieza + tokenización por separadores.
        partes = [p for p in _SEP_NUMERO.split(texto.strip()) if p]
        if not partes:
            return []
        # Cada parte debe ser puramente numérica (ignora basura).
        numeros = [p for p in partes if p.isdigit()]
        if not numeros:
            return []

        # Precarga: todas las palabras candidatas que vamos a consultar.
        candidatas: set[str] = set()
        for num in numeros:
            directa = NUMERO_DIRECTO.get(num)
            if directa:
                candidatas.add(directa)
            for d in num:
                if d in NUMERO_A_PALABRA:
                    candidatas.add(NUMERO_A_PALABRA[d])
        registros = self.diccionario.obtener_varias(sorted(candidatas))

        senas: list[Sena] = []
        for num in numeros:
            senas.extend(self._traducir_un_numero(num, registros, rol, clausula))
        return senas

    def _traducir_un_numero(
        self,
        num: str,
        registros: dict[str, dict[str, Any]],
        rol: str,
        clausula: int,
    ) -> list[Sena]:
        """Traduce un solo número entero usando los registros pre-cargados."""
        # 1) Seña directa (12, 100, 1000…) — solo si está cargada en BD.
        directa = NUMERO_DIRECTO.get(num)
        if directa and registros.get(directa):
            base = self._sena_desde_registro(registros[directa], rol=rol, clausula=clausula)
            return [Sena(
                palabra=base.palabra, gif_url=base.gif_url, tipo=base.tipo,
                encontrado=True, fuente="numero", rol=rol,
                media_type=base.media_type, clausula=clausula,
            )]

        # 2) Fallback dígito-a-dígito.
        salida: list[Sena] = []
        for d in num:
            palabra = NUMERO_A_PALABRA.get(d)
            if not palabra:
                continue
            entrada = registros.get(palabra)
            if entrada:
                base = self._sena_desde_registro(entrada, rol=rol, clausula=clausula)
                salida.append(Sena(
                    palabra=base.palabra, gif_url=base.gif_url, tipo=base.tipo,
                    encontrado=True, fuente="numero", rol=rol,
                    media_type=base.media_type, clausula=clausula,
                ))
            else:
                salida.append(Sena(
                    palabra=palabra, gif_url="", tipo="numero",
                    encontrado=False, fuente="no_disponible", rol=rol,
                    clausula=clausula,
                ))
        return salida

    def _deletrear(self, texto: str, rol: str = "otro", clausula: int = 0) -> list[Sena]:
        """Genera la secuencia de letras del alfabeto dactilológico."""
        letras = self.nlp.dividir_para_deletreo(texto)
        if not letras:
            return []
        registros = self.diccionario.obtener_varias(letras)
        senas: list[Sena] = []
        for letra in letras:
            entrada = registros.get(letra)
            if entrada:
                base = self._sena_desde_registro(entrada, rol=rol, clausula=clausula)
                senas.append(Sena(
                    palabra=base.palabra, gif_url=base.gif_url, tipo=base.tipo,
                    encontrado=True, fuente="deletreo", rol=rol,
                    media_type=base.media_type, clausula=clausula,
                ))
            else:
                senas.append(Sena(
                    palabra=letra, gif_url="", tipo="letra",
                    encontrado=False, fuente="no_disponible", rol=rol,
                    clausula=clausula,
                ))
        return senas
