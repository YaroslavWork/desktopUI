"""Random wallpaper from ~/Pictures/Wallpapers, swww + matugen → colors.css + bar theme reload."""

from __future__ import annotations

import json
import os
import random
import shlex
import subprocess
from pathlib import Path

from services.theme_service import reload_stylesheets

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WALLPAPER_DIR = Path.home() / "Pictures" / "Wallpapers"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jxl"}

# Material mapping: (colors.css variable name, matugen colors.* key)
_COLOR_PAIRS: tuple[tuple[str, str], ...] = (
    ("--background", "background"),
    ("--on-background", "on_background"),
    ("--surface", "surface"),
    ("--on-surface", "on_surface"),
    ("--surface-variant", "surface_variant"),
    ("--on-surface-variant", "on_surface_variant"),
    ("--primary", "primary"),
    ("--on-primary", "on_primary"),
    ("--primary-container", "primary_container"),
    ("--on-primary-container", "on_primary_container"),
    ("--secondary", "secondary"),
    ("--on-secondary", "on_secondary"),
    ("--secondary-container", "secondary_container"),
    ("--on-secondary-container", "on_secondary_container"),
    ("--tertiary", "tertiary"),
    ("--on-tertiary", "on_tertiary"),
    ("--tertiary-container", "tertiary_container"),
    ("--on-tertiary-container", "on_tertiary_container"),
    ("--error", "error"),
    ("--on-error", "on_error"),
    ("--error-container", "error_container"),
    ("--on-error-container", "on_error_container"),
    ("--outline", "outline"),
    ("--outline-variant", "outline_variant"),
    ("--shadow", "shadow"),
    ("--scrim", "scrim"),
)


def _list_wallpapers() -> list[Path]:
    if not WALLPAPER_DIR.is_dir():
        return []
    out: list[Path] = []
    for p in WALLPAPER_DIR.iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES:
            out.append(p)
    return out


def _pick_random_wallpaper() -> Path | None:
    files = _list_wallpapers()
    if not files:
        return None
    return random.choice(files)


def _hex_from_matugen(colors: dict, key: str, mode: str) -> str:
    node = colors.get(key)
    if not isinstance(node, dict):
        return "#808080"
    sub = node.get(mode) or node.get("default")
    if isinstance(sub, dict):
        c = sub.get("color")
        if isinstance(c, str) and c.startswith("#"):
            return c
    return "#808080"


def _write_colors_css_from_matugen(data: dict, mode: str) -> None:
    colors = data.get("colors")
    if not isinstance(colors, dict):
        return
    lines = [
        ":root {",
        "  /* Generated from matugen (desktopUI wallpaper action) */",
    ]
    for css_var, mg_key in _COLOR_PAIRS:
        lines.append(f"  {css_var}: {_hex_from_matugen(colors, mg_key, mode)};")
    lines.append("}")
    (PROJECT_ROOT / "colors.css").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_matugen(image: Path, mode: str) -> dict | None:
    if os.environ.get("DESKTOPUI_SKIP_MATUGEN", "").strip():
        return None
    cmd: list[str] = ["matugen"]
    cfg = os.environ.get("DESKTOPUI_MATUGEN_CONFIG", "").strip()
    if cfg:
        cmd.extend(["-c", cfg])
    cmd.extend(
        [
            "-m",
            mode,
            "-j",
            "hex",
            "--prefer",
            "value",
            "image",
            str(image.resolve()),
        ]
    )
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def _swww_set(image: Path) -> bool:
    """Apply wallpaper via swww (requires swww-daemon). Optional DESKTOPUI_SWWW_ARGS, e.g. --transition-type grow."""
    path = str(image.resolve())
    cmd: list[str] = ["swww", "img"]
    extra = os.environ.get("DESKTOPUI_SWWW_ARGS", "").strip()
    if extra:
        cmd.extend(shlex.split(extra))
    cmd.append(path)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def apply_random_wallpaper_and_theme() -> tuple[bool, str]:
    """
    Pick a random image, apply via swww img, run matugen, rewrite colors.css, reload Fabric CSS.
    Set DESKTOPUI_MATUGEN_MODE=light for light scheme. DESKTOPUI_SKIP_MATUGEN=1 skips matugen.
    DESKTOPUI_SWWW_ARGS='--transition-type center --transition-duration 2' for transitions.
    """
    img = _pick_random_wallpaper()
    if img is None:
        return False, f"No images in {WALLPAPER_DIR}"

    mode = os.environ.get("DESKTOPUI_MATUGEN_MODE", "dark").strip().lower()
    if mode not in ("dark", "light"):
        mode = "dark"

    if not _swww_set(img):
        return False, "swww failed (is `swww-daemon` running and `swww` in PATH?)"

    matugen_data = _run_matugen(img, mode)
    if matugen_data is not None:
        _write_colors_css_from_matugen(matugen_data, mode)

    reload_stylesheets()
    return True, str(img)


class WallpaperService:
    def apply_random(self) -> tuple[bool, str]:
        return apply_random_wallpaper_and_theme()


wallpaper_service = WallpaperService()
