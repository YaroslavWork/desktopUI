"""Load SVG icons from SVG/ folder as Gtk.Image."""

from pathlib import Path

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SVG_ROOT = PROJECT_ROOT / "SVG" / "Outline"

# Primary color for icon tinting (matches colors.css)
PRIMARY_COLOR = "#ffb68c"


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
            import tempfile
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


def load_icon(rel_path: str, size: int = 24, tint: bool = True) -> Gtk.Image | None:
    """Load icon from SVG/Outline. rel_path is like 'Time/Clock Circle.svg'."""
    path = SVG_ROOT / rel_path
    return _load_svg(path, size, PRIMARY_COLOR if tint else None)


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
