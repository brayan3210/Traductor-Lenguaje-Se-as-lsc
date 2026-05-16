"""Rutas para las páginas HTML servidas al usuario."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from models.diccionario import DiccionarioRepository

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing institucional."""
    return render_template("index.html")


@main_bp.route("/traductor")
def traductor():
    """Interfaz principal del traductor (dos paneles estilo Google Translate)."""
    return render_template("translator.html")


@main_bp.route("/diccionario")
def diccionario():
    """Vista exploradora del diccionario visual."""
    repo = DiccionarioRepository()
    categorias = repo.listar_categorias()
    return render_template("diccionario.html", categorias=categorias)


@main_bp.route("/ia")
def chat():
    """Asistente conversacional con un modelo local (GPT4All)."""
    return render_template("chat.html")


@main_bp.route("/login")
def login():
    return render_template("login.html")


@main_bp.route("/registro")
def registro():
    return render_template("register.html")


@main_bp.route("/login/2fa")
def login_2fa():
    return render_template("login_2fa.html")


@main_bp.route("/setup-2fa")
def setup_2fa():
    return render_template("setup_2fa.html")


@main_bp.route("/recuperar")
def recuperar():
    return render_template("recover.html")


@main_bp.route("/reset-password")
def reset_password():
    return render_template("reset_password.html", token=request.args.get("token", ""))


@main_bp.app_errorhandler(404)
def not_found(_error):
    return render_template("errors/404.html"), 404


@main_bp.app_errorhandler(500)
def server_error(_error):
    return render_template("errors/500.html"), 500
