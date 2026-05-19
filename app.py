"""Punto de entrada de la aplicación Señas Co — Traductor LSC.

Expone una factory `create_app()` para facilitar pruebas y despliegue.
"""
from __future__ import annotations

import logging
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from config.settings import Config, get_config
from database.connection import close_pool, init_pool
from models.recovery import PasswordResetRepository, RecoveryCodeRepository
from models.usuario import UsuarioRepository
from routes import api_bp, main_bp
from services.chat_service import get_chat_service


def _configurar_logging(nivel: int = logging.INFO) -> None:
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )


def create_app(config_name: str | None = None) -> Flask:
    _configurar_logging()

    app = Flask(__name__)
    config_cls = get_config(config_name)
    app.config.from_object(config_cls)
    app.config["JSON_AS_ASCII"] = False

    # Sesiones de cookie firmada (válidas 7 días).
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    CORS(app, supports_credentials=True)
    init_pool()

    # Garantiza tablas auxiliares (idempotente).
    try:
        UsuarioRepository().asegurar_tabla()
        RecoveryCodeRepository().asegurar_tabla()
        PasswordResetRepository().asegurar_tabla()
    except Exception:
        logging.getLogger(__name__).exception(
            "No se pudieron asegurar las tablas de auth al arrancar"
        )

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Pre-warmup del modelo de chat en background (controlado por
    # CHAT_WARMUP en .env). Arranca la carga del GGUF en un hilo aparte
    # para que la primera petición no pague el costo de cargar el modelo.
    #
    # IMPORTANTE: en `debug=True` Flask spawn DOS procesos (reloader parent
    # + worker child). Si lanzamos warmup en ambos, se carga el modelo dos
    # veces en memoria (≈10 GB en lugar de ≈5 GB). El reloader parent
    # nunca sirve requests, así que sólo necesitamos el modelo en el worker.
    # WERKZEUG_RUN_MAIN=true en el worker, ausente en el parent.
    en_worker = (not Config.DEBUG) or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if Config.CHAT_WARMUP and en_worker:
        try:
            get_chat_service().warmup_async()
        except Exception:
            logging.getLogger(__name__).warning(
                "No se pudo lanzar el pre-warmup del chat", exc_info=True
            )

    @app.context_processor
    def _inyectar_usuario():
        """Hace disponible `current_user` en todas las plantillas."""
        from flask import session
        user_id = session.get("user_id")
        if not user_id or session.get("pending_2fa"):
            return {"current_user": None}
        try:
            fila = UsuarioRepository().obtener_por_id(user_id)
            if not fila:
                return {"current_user": None}
            return {"current_user": {
                "id":        fila["id"],
                "nombres":   fila["nombres"],
                "apellidos": fila["apellidos"],
                "email":     fila["email"],
                "iniciales": (fila["nombres"][:1] + fila["apellidos"][:1]).upper(),
            }}
        except Exception:
            return {"current_user": None}

    @app.teardown_appcontext
    def _cleanup(_exc):
        close_pool()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
