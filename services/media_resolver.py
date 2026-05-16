"""Resolución dinámica del recurso multimedia (MP4 / GIF).

La BD almacena rutas con extensión `.gif` por compatibilidad histórica,
pero en disco puede estar el archivo en `.mp4` (mejor calidad, menor peso).
Este módulo resuelve **al vuelo** cuál de los dos existe y devuelve la URL
correcta junto con el tipo de medio.

Estrategia:
    1. Lee la URL declarada en BD (ej. `/static/gifs/palabras/comer.gif`).
    2. Mira la misma carpeta en disco buscando `comer.mp4`.
    3. Si existe el MP4 → lo prefiere (mejor calidad).
    4. Si no, busca el `.gif` original.
    5. Si tampoco, devuelve la URL declarada y el frontend mostrará el
       fallback "GIF pendiente / Sin seña".

Ventajas:
    · El usuario no necesita ejecutar SQL para cambiar extensiones.
    · Puede convivir cualquier mezcla de `.mp4` y `.gif` en la misma carpeta.
    · Cero acoplamiento con la lógica del traductor: el resolver es puro.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config.settings import Config

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(Config.BASE_DIR) / "static"

# Extensiones soportadas, en orden de preferencia.
_PREFERIDAS: tuple[tuple[str, str], ...] = (
    (".mp4", "video"),
    (".m4v", "video"),
    (".gif", "image"),
    (".webm", "video"),
)


@dataclass(frozen=True, slots=True)
class MediaResuelto:
    url: str
    media_type: str  # 'video' | 'image'
    existe: bool


def resolver(gif_url: str) -> MediaResuelto:
    """Resuelve la URL real del recurso en disco.

    Args:
        gif_url: ruta declarada en BD, ej. `/static/gifs/letras/a.gif`.

    Returns:
        MediaResuelto con la URL final, el `media_type` y `existe`.
        Si ningún archivo existe, devuelve la URL original con
        `existe=False` para que el frontend muestre el fallback.
    """
    if not gif_url:
        return MediaResuelto(url="", media_type="image", existe=False)

    rel_dir, stem = _descomponer(gif_url)
    if rel_dir is None:
        # URL externa o no anclada en /static — devolvemos tal cual.
        return MediaResuelto(
            url=gif_url,
            media_type=_tipo_por_extension(gif_url),
            existe=False,
        )

    carpeta_disco = _STATIC_DIR / rel_dir
    for ext, tipo in _PREFERIDAS:
        candidato = carpeta_disco / f"{stem}{ext}"
        if candidato.is_file():
            return MediaResuelto(
                url=_componer_url(rel_dir, stem, ext),
                media_type=tipo,
                existe=True,
            )

    # Nada en disco: devolvemos la URL declarada (con su extensión original).
    return MediaResuelto(
        url=gif_url,
        media_type=_tipo_por_extension(gif_url),
        existe=False,
    )


# ---------- Internos ----------

def _descomponer(gif_url: str) -> tuple[Path | None, str]:
    """Convierte `/static/gifs/palabras/comer.gif` en (`gifs/palabras`, `comer`)."""
    partes = Path(gif_url.lstrip("/")).parts
    if len(partes) < 2 or partes[0] != "static":
        return None, ""
    rel_path = Path(*partes[1:])
    return rel_path.parent, rel_path.stem


def _componer_url(rel_dir: Path, stem: str, ext: str) -> str:
    """Reconstruye la URL absoluta web (siempre con `/`, no con `\\`)."""
    sub = "/".join(rel_dir.parts) if rel_dir.parts else ""
    if sub:
        return f"/static/{sub}/{stem}{ext}"
    return f"/static/{stem}{ext}"


def _tipo_por_extension(url: str) -> str:
    low = url.lower()
    if low.endswith(".mp4") or low.endswith(".webm"):
        return "video"
    return "image"
