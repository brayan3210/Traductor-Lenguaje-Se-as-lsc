"""Servicio de chat conversacional con un modelo local de GPT4All.

Estrategia de rendimiento (de mayor a menor impacto):

  1. **GPU offload automático** (Vulkan/CUDA via `device='gpu'`)
        → 3–10x más rápido si hay GPU; cae a CPU si no.
  2. **Modelo configurable** (`CHAT_MODEL` env var)
        → cambiar Llama 3 8B → Phi-3 mini 3.8B da otro 2–3x extra.
  3. **Streaming token-a-token** vía callback de GPT4All
        → el usuario ve la respuesta nacer al instante.
  4. **Stop tokens** (\\nUsuario:, \\n\\n\\n)
        → el modelo termina en límite natural, no consume max_tokens en vano.
  5. **n_batch=256** + **max_tokens=300** balanceados.
  6. **Historial corto** (2 turnos) → menos prefill por petición.
  7. **Pre-warmup** del modelo al arrancar → 1ª petición sin latencia de carga.
"""
from __future__ import annotations

import logging
import os
import queue
import threading
from collections import deque
from typing import Iterator, Optional

from config.settings import Config

logger = logging.getLogger(__name__)


# System prompt: respuestas completas pero concisas, sin Markdown.
SYSTEM_PROMPT = (
    "Eres un asistente conversacional inteligente en español colombiano. "
    "Responde SIEMPRE en español, con claridad y precisión. "
    "Da respuestas completas pero concisas (entre 2 y 5 frases típicamente; "
    "más solo si el tema lo amerita). Sé directo, evita rodeos, no inventes "
    "datos. No uses Markdown, encabezados ni listas con guiones — habla en "
    "prosa natural. Si no sabes algo, dilo brevemente."
)

# Tokens que indican fin natural de respuesta. Si el modelo los emite,
# detenemos la generación de inmediato — evita que llene los max_tokens
# divagando o respondiendo por el usuario.
STOP_SEQUENCES: tuple[str, ...] = (
    "\nUsuario:",
    "\nUser:",
    "\n\nUsuario",
    "<|eot_id|>",
    "<|end_of_text|>",
    "<|im_end|>",
)


class ChatService:
    """Wrapper perezoso alrededor de gpt4all.GPT4All con streaming + GPU."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        self.model_name = model_name or Config.CHAT_MODEL
        self.device     = device or Config.CHAT_DEVICE
        self._model = None
        self._device_efectivo: str = "cpu"
        self._lock = threading.Lock()
        # Historial por session_id (deque acotada).
        self._historiales: dict[str, deque[tuple[str, str]]] = {}
        self._historial_lock = threading.Lock()

    # ---------- Carga del modelo ----------

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                from gpt4all import GPT4All
            except ImportError as exc:
                raise RuntimeError(
                    "El paquete 'gpt4all' no está instalado. "
                    "Instálalo con: pip install gpt4all"
                ) from exc

            # Fallback offline: GPT4All llama list_models() a internet
            # (gpt4all.io/models/models3.json) aunque el .gguf ya esté en
            # disco. Si la red falla, usamos un cache local. Solo se
            # aplica una vez (idempotente).
            _aplicar_fallback_offline()

            # Threads: si CHAT_N_THREADS está definido (≥1) en .env, lo usamos
            # tal cual; si no, autodetectamos como cores físicos (lógicos // 2),
            # mejor heurística para CPUs con SMT. El antiguo "lógicos - 1"
            # causaba contención severa en CPUs ultra-low-voltage como el
            # Ryzen 5 7520U (ver bench 2026-05-19: 4 threads = 4x más rápido).
            n_threads = Config.CHAT_N_THREADS or max((os.cpu_count() or 4) // 2, 2)
            logger.info(
                "Cargando modelo %s (device=%s, n_ctx=%d, threads=%d)",
                self.model_name, self.device, Config.CHAT_N_CTX, n_threads,
            )

            # Intentamos GPU primero; si falla (no hay driver compatible),
            # caemos a CPU automáticamente.
            try:
                self._model = GPT4All(
                    self.model_name,
                    allow_download=True,
                    n_threads=n_threads,
                    n_ctx=Config.CHAT_N_CTX,
                    device=self.device,
                )
                self._device_efectivo = self.device
                logger.info("Modelo cargado en device=%s", self.device)
            except Exception as exc:
                if self.device == "cpu":
                    raise
                logger.warning(
                    "GPU no disponible (%s). Reintentando en CPU.", exc,
                )
                self._model = GPT4All(
                    self.model_name,
                    allow_download=True,
                    n_threads=n_threads,
                    n_ctx=Config.CHAT_N_CTX,
                    device="cpu",
                )
                self._device_efectivo = "cpu"
                logger.info("Modelo cargado en device=cpu (fallback)")
        return self._model

    def warmup_async(self) -> None:
        """Carga el modelo en background al arrancar la app."""
        def _do_load():
            try:
                self._ensure_model()
            except Exception:
                logger.warning("Pre-warmup del modelo de chat falló", exc_info=True)

        threading.Thread(target=_do_load, name="chat-warmup", daemon=True).start()

    def info(self) -> dict:
        """Información diagnóstica del estado del modelo."""
        return {
            "modelo":            self.model_name,
            "device_solicitado": self.device,
            "device_efectivo":   self._device_efectivo,
            "cargado":           self._model is not None,
            "max_tokens":        Config.CHAT_MAX_TOKENS,
            "n_batch":           Config.CHAT_N_BATCH,
            "n_ctx":             Config.CHAT_N_CTX,
            "historial_turnos":  Config.CHAT_HISTORIAL,
        }

    # ---------- Historial ----------

    def _construir_prompt(self, session_id: str, mensaje: str) -> str:
        """Arma el prompt con los últimos turnos para dar continuidad."""
        with self._historial_lock:
            historial = list(self._historiales.get(session_id, ()))
        if not historial:
            return mensaje
        partes: list[str] = []
        for usuario, bot in historial:
            partes.append(f"Usuario: {usuario}")
            partes.append(f"Asistente: {bot}")
        partes.append(f"Usuario: {mensaje}")
        partes.append("Asistente:")
        return "\n".join(partes)

    def _guardar_turno(self, session_id: str, usuario: str, bot: str) -> None:
        bot = (bot or "").strip()
        if not bot:
            return
        with self._historial_lock:
            cola = self._historiales.setdefault(
                session_id, deque(maxlen=Config.CHAT_HISTORIAL)
            )
            cola.append((usuario, bot))

    def limpiar_historial(self, session_id: str) -> None:
        with self._historial_lock:
            self._historiales.pop(session_id, None)

    # ---------- Helpers de generación ----------

    @staticmethod
    def _truncar_por_stop(texto: str) -> str:
        """Corta el texto si aparece alguna stop sequence."""
        idx_min = -1
        for stop in STOP_SEQUENCES:
            i = texto.find(stop)
            if i != -1 and (idx_min == -1 or i < idx_min):
                idx_min = i
        if idx_min == -1:
            return texto
        return texto[:idx_min]

    def _gen_kwargs(self, max_tokens: int) -> dict:
        return dict(
            max_tokens=max_tokens,
            temp=0.6,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.12,
            n_batch=Config.CHAT_N_BATCH,
        )

    # ---------- Generación NO-streaming (compatibilidad) ----------

    def responder(
        self, mensaje: str, session_id: str = "default",
        max_tokens: Optional[int] = None,
    ) -> str:
        mensaje = (mensaje or "").strip()
        if not mensaje:
            raise ValueError("El mensaje no puede estar vacío")

        model = self._ensure_model()
        prompt = self._construir_prompt(session_id, mensaje)
        max_tokens = max_tokens or Config.CHAT_MAX_TOKENS

        with self._lock:
            with model.chat_session(system_prompt=SYSTEM_PROMPT):
                respuesta = model.generate(prompt, **self._gen_kwargs(max_tokens))
        respuesta = self._truncar_por_stop((respuesta or "")).strip()
        self._guardar_turno(session_id, mensaje, respuesta)
        return respuesta

    # ---------- Generación STREAMING ----------

    def responder_stream(
        self, mensaje: str, session_id: str = "default",
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Emite los tokens de la respuesta conforme se generan."""
        mensaje = (mensaje or "").strip()
        if not mensaje:
            raise ValueError("El mensaje no puede estar vacío")

        model = self._ensure_model()
        prompt = self._construir_prompt(session_id, mensaje)
        max_tokens = max_tokens or Config.CHAT_MAX_TOKENS

        cola: queue.Queue[Optional[str]] = queue.Queue(maxsize=256)
        acumulado: list[str] = []
        # Caja para que el callback pueda señalar "aborta esta generación".
        abort_flag = {"abort": False}

        def _callback(token_id: int, token_text: str) -> bool:  # noqa: ARG001
            acumulado.append(token_text)
            cola.put(token_text)
            # Si el modelo emitió una stop sequence, abortamos para no
            # malgastar tokens. Solo chequeamos los últimos ~120 chars
            # (suficiente para detectar "\nUsuario:" etc.).
            tail = "".join(acumulado)[-120:]
            for stop in STOP_SEQUENCES:
                if stop in tail:
                    abort_flag["abort"] = True
                    return False
            return True

        respuesta_final: list[str] = [""]
        error_holder: list[BaseException] = []

        def _worker() -> None:
            try:
                with self._lock:
                    with model.chat_session(system_prompt=SYSTEM_PROMPT):
                        model.generate(
                            prompt,
                            streaming=True,
                            callback=_callback,
                            **self._gen_kwargs(max_tokens),
                        )
            except BaseException as exc:  # noqa: BLE001
                error_holder.append(exc)
            finally:
                respuesta_final[0] = self._truncar_por_stop("".join(acumulado))
                cola.put(None)  # sentinel

        threading.Thread(target=_worker, name="chat-gen", daemon=True).start()

        # Emisión al cliente. Si detectamos stop sequence en el flujo,
        # cortamos antes de emitir el token problemático.
        emitido = ""
        while True:
            token = cola.get()
            if token is None:
                break
            siguiente = emitido + token
            truncado = self._truncar_por_stop(siguiente)
            if truncado != siguiente:
                # Llegamos a una stop sequence: emitimos solo el prefijo
                # nuevo (sin el stop) y dejamos de emitir.
                nuevo = truncado[len(emitido):]
                if nuevo:
                    yield nuevo
                emitido = truncado
                # Drenamos la cola sin emitir para que el worker no se bloquee.
                while True:
                    t = cola.get()
                    if t is None:
                        break
                continue
            yield token
            emitido = siguiente

        if error_holder:
            logger.exception("Error durante stream del chat", exc_info=error_holder[0])
            raise error_holder[0]

        self._guardar_turno(session_id, mensaje, respuesta_final[0].strip())


_offline_patch_aplicado = False


def _aplicar_fallback_offline() -> None:
    """Parchea `GPT4All.list_models` para usar `~/.cache/gpt4all/models3.json`
    si la red falla. Idempotente. La primera vez que arrancas con red, el
    manifest se descarga normalmente (gpt4all lo hace al instanciar
    GPT4All); puedes refrescarlo manualmente con::

        curl -o ~/.cache/gpt4all/models3.json https://gpt4all.io/models/models3.json
    """
    global _offline_patch_aplicado
    if _offline_patch_aplicado:
        return
    _offline_patch_aplicado = True
    import json
    from pathlib import Path
    from gpt4all import GPT4All as _G4A
    cache_file = Path.home() / ".cache" / "gpt4all" / "models3.json"
    original = _G4A.list_models
    def _patched():
        try:
            return original()
        except Exception as exc:
            if cache_file.exists():
                logger.warning(
                    "Sin red para gpt4all.io — usando manifest local en %s (%s)",
                    cache_file, exc,
                )
                return json.loads(cache_file.read_text(encoding="utf-8"))
            raise
    _G4A.list_models = staticmethod(_patched)


_singleton: Optional[ChatService] = None
_singleton_lock = threading.Lock()


def get_chat_service() -> ChatService:
    """Devuelve la instancia única del servicio de chat."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = ChatService()
    return _singleton
