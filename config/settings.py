"""Configuración centralizada de la aplicación.

Todas las opciones se leen desde variables de entorno (.env) con valores
por defecto pensados para el entorno de desarrollo con XAMPP.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config:
    """Configuración base compartida por todos los entornos."""

    BASE_DIR: Path = BASE_DIR

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-cambiar-en-produccion")
    DEBUG: bool = _env_bool("FLASK_DEBUG", True)

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = _env_int("PORT", 5000)

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = _env_int("DB_PORT", 3306)
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "traductor_lsc")
    DB_CHARSET: str = "utf8mb4"

    SPACY_MODEL: str = os.getenv("SPACY_MODEL", "es_core_news_sm")
    MAX_TOKENS: int = _env_int("MAX_TOKENS", 80)

    GIFS_LETRAS_DIR: str = "gifs/letras"
    GIFS_PALABRAS_DIR: str = "gifs/palabras"

    JSON_AS_ASCII: bool = False

    # ---------- Email (SMTP) ----------
    SMTP_HOST: str         = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int         = _env_int("SMTP_PORT", 587)
    SMTP_USER: str         = os.getenv("SMTP_USER", "")
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "")
    SMTP_FROM_NAME: str    = os.getenv("SMTP_FROM_NAME", "Señas Co")
    APP_BASE_URL: str      = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")

    # ---------- 2FA / TOTP ----------
    TOTP_ISSUER: str = os.getenv("TOTP_ISSUER", "Señas Co")

    # ---------- Google OAuth ----------
    GOOGLE_CLIENT_ID: str     = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str  = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5000/api/auth/google/callback",
    )

    # ---------- Chat IA (GPT4All / llama.cpp) ----------
    # Modelo a usar. Por defecto el Llama 3 8B que ya tiene el usuario.
    # Para 3x más velocidad cambiar a un modelo 3B, ej:
    #   CHAT_MODEL=Phi-3-mini-4k-instruct.Q4_0.gguf
    #   CHAT_MODEL=qwen2-1_5b-instruct-q4_0.gguf
    # GPT4All los descarga automáticamente la primera vez.
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
    # Dispositivo: 'cpu', 'gpu' (auto-detect Vulkan/CUDA), 'nvidia', 'amd',
    # 'intel'. 'gpu' es el modo recomendado: GPT4All cae a CPU si no hay GPU.
    CHAT_DEVICE: str = os.getenv("CHAT_DEVICE", "gpu")
    CHAT_MAX_TOKENS: int = _env_int("CHAT_MAX_TOKENS", 300)
    CHAT_N_CTX: int      = _env_int("CHAT_N_CTX", 2048)
    CHAT_N_BATCH: int    = _env_int("CHAT_N_BATCH", 256)
    # Threads de inferencia. 0 = autodetectar como cores físicos (lógicos // 2),
    # mejor heurística para CPUs con SMT que la antigua "lógicos - 1" que
    # causaba contención severa en Ryzen low-voltage. Override útil si el
    # usuario tiene un CPU sin SMT (poner = núm cores).
    CHAT_N_THREADS: int  = _env_int("CHAT_N_THREADS", 0)
    # Cuántos turnos previos mantener en memoria (más turnos = más prefill).
    CHAT_HISTORIAL: int  = _env_int("CHAT_HISTORIAL", 2)
    # Lanzar la carga del modelo en background al arrancar la app.
    CHAT_WARMUP: bool    = _env_bool("CHAT_WARMUP", True)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY", "")


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    """Selecciona la clase de configuración según FLASK_ENV o el argumento."""
    if name is None:
        name = os.getenv("FLASK_ENV", "development")
    return _CONFIG_MAP.get(name, DevelopmentConfig)
