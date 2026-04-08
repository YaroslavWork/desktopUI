"""GTK button for a Hyprland window (icon / letter); used inside combined workspace strips."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.button import Button

from services.workspace_apps_service import WorkspaceApp
from widgets.bar_app_pill import build_bar_app_pill_button, set_bar_pill_active


def _get_app_display(app: WorkspaceApp) -> tuple[str, str]:
    """GTK icon name (may be empty) and a single letter for fallback."""
    cls = (app.app_class or "").strip()
    icon_name = cls.lower().replace(" ", "-") if cls else ""
    name_for_letter = cls or (app.title or "").strip() or "?"
    letter = name_for_letter[0].upper()
    return (icon_name, letter)


def _on_app_clicked(_btn: Button, app: WorkspaceApp) -> None:
    try:
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{app.address}"],
            capture_output=True,
            timeout=1,
        )
    except (subprocess.SubprocessError, OSError):
        pass


def build_workspace_app_button(app: WorkspaceApp) -> Button:
    """Round button: themed icon when available, otherwise first letter of class or title."""
    icon_name, _ = _get_app_display(app)
    letter_source = (app.app_class or app.title or "").strip() or "?"
    btn = build_bar_app_pill_button(
        icon_name_candidate=icon_name,
        letter_source=letter_source,
        tooltip=app.title or app.app_class or "",
    )
    btn.connect("clicked", _on_app_clicked, app)
    setattr(btn, "_desktopui_app_address", app.address)
    return btn


def set_app_button_active(btn: Button, active: bool) -> None:
    set_bar_pill_active(btn, active)
