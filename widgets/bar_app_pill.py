"""Round bar pills: themed GTK icon or single letter — shared by workspace apps and MPRIS source row."""

from __future__ import annotations

import sys
from pathlib import Path

# Importing fabric requires project root on path when this module loads first.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from fabric.widgets.button import Button

APP_ICON_PIXEL = 18
BUTTON_PIXEL = 28


def gtk_icon_name_from_class_str(s: str) -> str:
    return (s or "").strip().lower().replace(" ", "-")


def single_letter_from_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return "?"
    return n[0].upper()


def themed_icon_image(icon_name: str, size: int = APP_ICON_PIXEL) -> Gtk.Image | None:
    if not icon_name:
        return None
    try:
        theme = Gtk.IconTheme.get_default()
        name = gtk_icon_name_from_class_str(icon_name)
        if not name or not theme.has_icon(name):
            return None
        pixbuf = theme.load_icon(name, size, Gtk.IconLookupFlags.FORCE_SIZE)
        img = Gtk.Image.new_from_pixbuf(pixbuf)
        img.set_halign(Gtk.Align.CENTER)
        img.set_valign(Gtk.Align.CENTER)
        return img
    except GLib.Error:
        return None


def single_letter_label(letter: str) -> Gtk.Label:
    lab = Gtk.Label(label=letter)
    lab.set_xalign(0.5)
    lab.set_max_width_chars(1)
    lab.set_width_chars(1)
    lab.set_line_wrap(False)
    lab.set_halign(Gtk.Align.CENTER)
    lab.set_valign(Gtk.Align.CENTER)
    lab.set_vexpand(False)
    lab.set_hexpand(False)
    return lab


def build_bar_app_pill_button(
    *,
    icon_name_candidate: str,
    letter_source: str,
    tooltip: str,
) -> Button:
    """Same look as workspace app chips: 28×28 circle, icon or one letter."""
    hint = gtk_icon_name_from_class_str(icon_name_candidate)
    img = themed_icon_image(hint) if hint else None
    if img is not None:
        btn = Button(
            child=img,
            style_classes=["workspace-app-button", "flat"],
            size=(BUTTON_PIXEL, BUTTON_PIXEL),
            v_align="center",
        )
    else:
        btn = Button(
            child=single_letter_label(single_letter_from_name(letter_source)),
            style_classes=["workspace-app-button", "workspace-app-letter", "flat"],
            size=(BUTTON_PIXEL, BUTTON_PIXEL),
            v_align="center",
        )
    btn.set_relief(Gtk.ReliefStyle.NONE)
    btn.set_hexpand(False)
    btn.set_vexpand(False)
    btn.set_size_request(BUTTON_PIXEL, BUTTON_PIXEL)
    btn.set_tooltip_text(tooltip)
    return btn


def set_bar_pill_active(btn: Button, active: bool) -> None:
    ctx = btn.get_style_context()
    if active:
        ctx.add_class("active")
    else:
        ctx.remove_class("active")
