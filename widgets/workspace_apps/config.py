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


def _letter_label(text: str) -> Gtk.Label:
    """Single-line label sized like one glyph so the parent button stays square."""
    lab = Gtk.Label(label=text)
    lab.set_xalign(0.5)
    lab.set_max_width_chars(1)
    lab.set_width_chars(1)
    lab.set_line_wrap(False)
    lab.set_halign(Gtk.Align.CENTER)
    lab.set_valign(Gtk.Align.CENTER)
    lab.set_vexpand(False)
    lab.set_hexpand(False)
    return lab


def build_workspace_app_button(app: WorkspaceApp) -> Button:
    """Round button: themed icon when available, otherwise first letter of class or title."""
    icon_name, letter = _get_app_display(app)
    try:
        theme = Gtk.IconTheme.get_default()
        if icon_name and theme.has_icon(icon_name):
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            img.set_halign(Gtk.Align.CENTER)
            img.set_valign(Gtk.Align.CENTER)
            btn = Button(
                child=img,
                style_classes=["workspace-app-button", "flat"],
                size=(28, 28),
                v_align="center",
            )
        else:
            btn = Button(
                child=_letter_label(letter),
                style_classes=["workspace-app-button", "workspace-app-letter", "flat"],
                size=(28, 28),
                v_align="center",
            )
    except Exception:
        btn = Button(
            child=_letter_label(letter),
            style_classes=["workspace-app-button", "workspace-app-letter", "flat"],
            size=(28, 28),
            v_align="center",
        )
    btn.set_relief(Gtk.ReliefStyle.NONE)
    btn.set_hexpand(False)
    btn.set_vexpand(False)
    btn.set_size_request(28, 28)
    btn.set_tooltip_text(app.title or app.app_class)
    btn.connect("clicked", _on_app_clicked, app)
    setattr(btn, "_desktopui_app_address", app.address)
    return btn


def set_app_button_active(btn: Button, active: bool) -> None:
    ctx = btn.get_style_context()
    if active:
        ctx.add_class("active")
    else:
        ctx.remove_class("active")
