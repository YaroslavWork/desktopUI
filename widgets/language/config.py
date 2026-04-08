"""Keyboard layout indicator (PL, US, …) for Hyprland; pulses when layout changes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

from services.keyboard_layout_service import snapshot as layout_snapshot

POLL_MS = 400


class LanguageWidget(Box):
    """Short layout code from main keyboard; double pulse on change."""

    def __init__(self, **kwargs):
        self._label = Label(
            label="—",
            style_classes=["language-widget-label"],
        )
        self._label.set_xalign(0.5)
        self._label.set_yalign(0.5)
        self._label.set_hexpand(True)
        self._label.set_vexpand(True)
        self._label.set_halign(Gtk.Align.FILL)
        self._label.set_valign(Gtk.Align.FILL)

        super().__init__(
            orientation="horizontal",
            spacing=0,
            style_classes=["language-widget"],
            children=[self._label],
            **kwargs,
        )
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self.set_tooltip_text("Keyboard layout (main device, Hyprland)")
        self._last_fp: str | None = None
        self._initialized = False
        self._flash_source: int | None = None

        invoke_repeater(POLL_MS, self._tick)
        self.connect("destroy", lambda *_: self._cancel_flash_timeouts())
        self._tick()

    def _cancel_flash_timeouts(self) -> None:
        if self._flash_source is not None:
            GLib.source_remove(self._flash_source)
            self._flash_source = None

    def _pulse_on(self, duration_ms: int) -> None:
        self.get_style_context().add_class("language-widget-pulse")
        self._cancel_flash_timeouts()
        self._flash_source = GLib.timeout_add(duration_ms, self._pulse_off_mid)

    def _pulse_off_mid(self) -> bool:
        self._flash_source = None
        self.get_style_context().remove_class("language-widget-pulse")
        self._flash_source = GLib.timeout_add(90, self._pulse_second_on)
        return False

    def _pulse_second_on(self) -> bool:
        self._flash_source = None
        self.get_style_context().add_class("language-widget-pulse")
        self._flash_source = GLib.timeout_add(200, self._pulse_end)
        return False

    def _pulse_end(self) -> bool:
        self._flash_source = None
        self.get_style_context().remove_class("language-widget-pulse")
        return False

    def _flash(self) -> None:
        self._pulse_on(200)

    def _tick(self) -> bool:
        label, fp = layout_snapshot()
        self._label.set_label(label)
        if fp is not None:
            if self._initialized and self._last_fp is not None and fp != self._last_fp:
                self._flash()
            self._last_fp = fp
            self._initialized = True
        return True
