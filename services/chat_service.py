"""Servicio de chat conversacional con un modelo local de GPT4All.

Carga el modelo en modo perezoso (la primera petición lo descarga si hace
falta) y expone un método `responder` síncrono. Mantenemos la lógica
deliberadamente simple: una sola sesión global, sin streaming, sin
historial — solo prompt → respuesta.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)


# Llama 3 8B Instruct (Q4_0, ≈4.66 GB). El usuario ya lo tiene descargado
# en ~/.cache/gpt4all. Si no, GPT4All lo descarga automáticamente.
DEFAULT_MODEL = "Meta-Llama-3-8B-Instruct.Q4_0.gguf"

SYSTEM_PROMPT = (
    "Eres un asistente conversacional en español. Responde SIEMPRE en español, "
    "de forma muy breve (1 a 3 frases), directa y clara. Sin rodeos ni listas."
)


class ChatService:
    """Wrapper perezoso alrededor de gpt4all.GPT4All."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                try:
                    from gpt4all import GPT4All
                except ImportError as exc:
                    raise RuntimeError(
                        "El paquete 'gpt4all' no está instalado. "
                        "Instálalo con: pip install gpt4all"
                    ) from exc
                logger.info("Cargando modelo GPT4All: %s", self.model_name)
                self._model = GPT4All(
                    self.model_name,
                    allow_download=True,
                    n_threads=max((os.cpu_count() or 4) - 1, 2),
                )
                logger.info("Modelo cargado correctamente")
        return self._model

    def responder(self, mensaje: str, max_tokens: int = 160) -> str:
        mensaje = (mensaje or "").strip()
        if not mensaje:
            raise ValueError("El mensaje no puede estar vacío")

        model = self._ensure_model()

        with self._lock:
            with model.chat_session(system_prompt=SYSTEM_PROMPT):
                respuesta = model.generate(
                    mensaje,
                    max_tokens=max_tokens,
                    temp=0.6,
                    top_p=0.9,
                    repeat_penalty=1.15,
                )
        return (respuesta or "").strip()


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
