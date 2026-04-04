"""Load SVG icons from SVG/ folder as Gtk.Image."""

import re
import tempfile
from pathlib import Path

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVG_ROOT = PROJECT_ROOT / "SVG" / "Outline"

# Fallback when colors.css is missing or unparsable (must stay in sync with a sane default theme)
PRIMARY_FALLBACK = "#ffb68c"
SECONDARY_FALLBACK = "#e5bfaa"
TERTIARY_FALLBACK = "#e8b9d5"

_PRIMARY_RE = re.compile(
    r"--primary:\s*(#[0-9A-Fa-f]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\))\s*;",
    re.MULTILINE,
)
_SECONDARY_RE = re.compile(
    r"--secondary:\s*(#[0-9A-Fa-f]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\))\s*;",
    re.MULTILINE,
)
_TERTIARY_RE = re.compile(
    r"--tertiary:\s*(#[0-9A-Fa-f]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\))\s*;",
    re.MULTILINE,
)


def read_primary_tint_hex() -> str:
    """Read --primary from project colors.css for SVG tinting (matugen updates this file)."""
    path = PROJECT_ROOT / "colors.css"
    if not path.is_file():
        return PRIMARY_FALLBACK
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return PRIMARY_FALLBACK
    m = _PRIMARY_RE.search(text)
    if not m:
        return PRIMARY_FALLBACK
    value = m.group(1).strip()
    if value.startswith("#") and len(value) in (4, 5, 7, 9):
        return value
    return PRIMARY_FALLBACK


def read_secondary_tint_hex() -> str:
    """Read --secondary from colors.css (weather icon + temperature accent)."""
    path = PROJECT_ROOT / "colors.css"
    if not path.is_file():
        return SECONDARY_FALLBACK
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return SECONDARY_FALLBACK
    m = _SECONDARY_RE.search(text)
    if not m:
        return SECONDARY_FALLBACK
    value = m.group(1).strip()
    if value.startswith("#") and len(value) in (4, 5, 7, 9):
        return value
    return SECONDARY_FALLBACK


def read_tertiary_tint_hex() -> str:
    """Read --tertiary from colors.css (weather icon gradient end stop)."""
    path = PROJECT_ROOT / "colors.css"
    if not path.is_file():
        return TERTIARY_FALLBACK
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return TERTIARY_FALLBACK
    m = _TERTIARY_RE.search(text)
    if not m:
        return TERTIARY_FALLBACK
    value = m.group(1).strip()
    if value.startswith("#") and len(value) in (4, 5, 7, 9):
        return value
    return TERTIARY_FALLBACK


def _svg_apply_primary_tertiary_gradient(content: str, grad_id: str, primary: str, tertiary: str) -> str:
    """Inject a vertical linearGradient and paint former black fills/strokes with it."""
    defs = (
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{primary}"/>'
        f'<stop offset="100%" stop-color="{tertiary}"/></linearGradient></defs>'
    )
    m = re.match(r"(<svg[^>]*>)", content, re.DOTALL)
    if m:
        content = m.group(1) + defs + content[m.end() :]
    else:
        content = defs + content
    url = f"url(#{grad_id})"
    content = content.replace('fill="black"', f'fill="{url}"')
    content = content.replace("fill='black'", f"fill='{url}'")
    content = content.replace('stroke="black"', f'stroke="{url}"')
    content = content.replace("stroke='black'", f"stroke='{url}'")
    return content


def _load_svg(path: Path, size: int, color: str | None = None) -> Gtk.Image | None:
    """Load SVG as Gtk.Image. Optionally replace black with color."""
    if not path.exists():
        return None
    try:
        if color:
            content = path.read_text()
            content = content.replace('fill="black"', f'fill="{color}"')
            content = content.replace("fill='black'", f"fill='{color}'")
            content = content.replace('stroke="black"', f'stroke="{color}"')
            # Write to temp and load - GdkPixbuf needs file path
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
                f.write(content.encode())
                tmp = f.name
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(tmp, size, size)
                return Gtk.Image.new_from_pixbuf(pb)
            finally:
                Path(tmp).unlink(missing_ok=True)
        else:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(str(path), size, size)
            return Gtk.Image.new_from_pixbuf(pb)
    except Exception:
        return None


def load_icon(
    rel_path: str,
    size: int = 24,
    tint: bool = True,
    *,
    primary: bool = True,
) -> Gtk.Image | None:
    """Load icon from SVG/Outline. rel_path is like 'Time/Clock Circle.svg'."""
    path = SVG_ROOT / rel_path
    if not tint:
        color = None
    else:
        color = read_primary_tint_hex() if primary else read_secondary_tint_hex()
    return _load_svg(path, size, color)


def load_weather_icon(rel_path: str, size: int = 24) -> Gtk.Image | None:
    """Weather glyph with a vertical SVG gradient from --primary (top) to --tertiary (bottom)."""
    path = SVG_ROOT / rel_path
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        grad_id = "desktopuiWeatherGrad"
        colored = _svg_apply_primary_tertiary_gradient(
            raw,
            grad_id,
            read_primary_tint_hex(),
            read_tertiary_tint_hex(),
        )
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            f.write(colored.encode("utf-8"))
            tmp = f.name
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(tmp, size, size)
            return Gtk.Image.new_from_pixbuf(pb)
        finally:
            Path(tmp).unlink(missing_ok=True)
    except Exception:
        return None


# Workspace icons: Sun + 8 planet variants
WORKSPACE_ICONS = [
    "Weather/Sun.svg",
    "Astronomy/Planet.svg",
    "Astronomy/Planet 2.svg",
    "Astronomy/Earth.svg",
    "Astronomy/Planet 3.svg",
    "Astronomy/Planet 4.svg",
    "Astronomy/Planet.svg",   # repeat
    "Astronomy/Planet 2.svg",
    "Astronomy/Planet 3.svg",
]

# Standard icons
ICON_CLOCK = "Time/Clock Circle.svg"
ICON_USER = "Users/User.svg"
ICON_WINDOW = "Network, IT, Programming/Window Frame.svg"
ICON_SETTINGS = "Settings, Fine Tuning/Settings.svg"
ICON_LOGOUT = "Arrows Action/Logout.svg"
ICON_LOCK = "Security/Lock Keyhole Minimalistic.svg"
ICON_POWER = "Essentional, UI/Power.svg"
ICON_PLAY = "Video, Audio, Sound/Play.svg"
ICON_PAUSE = "Video, Audio, Sound/Pause.svg"
ICON_SKIP_PREV = "Video, Audio, Sound/Skip Previous.svg"
ICON_SKIP_NEXT = "Video, Audio, Sound/Skip Next.svg"


def clock_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_CLOCK, size)


def user_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_USER, size)


def window_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_WINDOW, size)


def workspace_icon(index: int, size: int = 24) -> Gtk.Image | None:
    """Load icon for workspace 1-9. Index 0 = Sun, 1-8 = planets."""
    if 0 <= index < len(WORKSPACE_ICONS):
        return load_icon(WORKSPACE_ICONS[index], size)
    return None


def settings_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_SETTINGS, size)


def logout_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_LOGOUT, size)


def lock_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_LOCK, size)


def power_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_POWER, size)


def play_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_PLAY, size)


def pause_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_PAUSE, size)


def skip_prev_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_SKIP_PREV, size)


def skip_next_icon(size: int = 24) -> Gtk.Image | None:
    return load_icon(ICON_SKIP_NEXT, size)
