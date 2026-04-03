"""Centered overlay: pick one active Hyprland display or use all displays."""

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow

from services.displays_service import displays_service


def _style_radio(rb: Gtk.RadioButton) -> None:
    rb.get_style_context().add_class("display-settings-radio")


def _monitor_label(m: dict) -> str:
    name = str(m.get("name", "?"))
    w = int(m.get("width", 0))
    h = int(m.get("height", 0))
    rr = float(m.get("refreshRate", 0.0))
    focused = m.get("focused")
    star = " · focused" if focused else ""
    return f"{name} — {w}×{h} @ {rr:.1f} Hz{star}"


class DisplaySettingsContent(Box):
    """Radio: use all displays, or exactly one active display; Apply / Close."""

    def __init__(self, on_close: Callable[[], None], **kwargs):
        self._on_close = on_close
        self._monitors: list[dict] = []
        self._radio_all: Gtk.RadioButton | None = None
        self._radio_rows: list[tuple[str, Gtk.RadioButton]] = []
        self._list_box = Box(orientation="vertical", spacing=10, style_classes=["display-settings-list"])

        title = Label(
            label="Display Settings",
            style_classes=["display-settings-title"],
        )
        title.set_xalign(0.0)

        hint = Label(
            label="Hyprland: one active output disables the others. Re-connect or run "
            "hyprctl keyword monitor NAME,preferred,auto,1 if a screen stays off.",
            style_classes=["display-settings-hint"],
        )
        hint.set_line_wrap(True)
        hint.set_max_width_chars(42)
        hint.set_xalign(0.0)

        apply_btn = Button(
            label="Apply",
            style_classes=["display-settings-apply", "flat"],
            size=(120, 36),
        )
        apply_btn.set_relief(Gtk.ReliefStyle.NONE)
        apply_btn.connect("clicked", self._on_apply)

        close_btn = Button(
            label="Close",
            style_classes=["display-settings-close", "flat"],
            size=(120, 36),
        )
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.connect("clicked", lambda *_: self._on_close())

        actions = Box(
            orientation="horizontal",
            spacing=12,
            style_classes=["display-settings-actions"],
            children=[apply_btn, close_btn],
        )

        super().__init__(
            orientation="vertical",
            spacing=14,
            style_classes=["display-settings-widget"],
            children=[title, hint, self._list_box, actions],
            **kwargs,
        )

    def refresh_list(self) -> None:
        self._monitors = displays_service.list_monitors()
        for w in self._list_box.get_children():
            self._list_box.remove(w)
        self._radio_all = None
        self._radio_rows.clear()

        if not self._monitors:
            self._list_box.add(
                Label(
                    label="No monitors found (is Hyprland running?)",
                    style_classes=["display-settings-empty"],
                )
            )
            self._list_box.show_all()
            return

        self._radio_all = Gtk.RadioButton.new_with_label(
            None, "Use all displays (enable every output below)"
        )
        _style_radio(self._radio_all)
        self._list_box.add(self._radio_all)

        for m in self._monitors:
            name = str(m.get("name", ""))
            rb = Gtk.RadioButton.new_with_label_from_widget(self._radio_all, _monitor_label(m))
            _style_radio(rb)
            self._list_box.add(rb)
            self._radio_rows.append((name, rb))

        focused_name: str | None = None
        for m in self._monitors:
            if m.get("focused"):
                focused_name = str(m.get("name", ""))
                break
        if focused_name:
            for name, rb in self._radio_rows:
                if name == focused_name:
                    rb.set_active(True)
                    break
            else:
                self._radio_all.set_active(True)
        else:
            self._radio_all.set_active(True)

        self._list_box.show_all()

    def _on_apply(self, _btn) -> None:
        if not self._monitors:
            return
        if self._radio_all and self._radio_all.get_active():
            ok, msg = displays_service.apply_all_enabled(self._monitors)
            if not ok and msg:
                _btn.set_tooltip_text(msg)
            return
        for name, rb in self._radio_rows:
            if rb.get_active():
                ok, msg = displays_service.apply_single_active(self._monitors, name)
                if not ok and msg:
                    _btn.set_tooltip_text(msg)
                return


class DisplaySettingsPopup(WaylandWindow):
    """Centered overlay for display mode selection."""

    def __init__(self, **kwargs):
        self._content = DisplaySettingsContent(on_close=self.hide)
        super().__init__(
            layer="overlay",
            anchor="top bottom left right",
            margin="0px 0px 0px 0px",
            exclusivity="none",
            keyboard_mode="on-demand",
            style_classes=["display-settings-popup"],
            **kwargs,
        )
        inner = Box(
            orientation="vertical",
            style_classes=["display-settings-popup-inner"],
            children=[self._content],
        )
        self.children = Box(
            orientation="vertical",
            h_expand=True,
            v_expand=True,
            h_align="center",
            v_align="center",
            children=[inner],
        )
        self.hide()

    def open_centered(self) -> None:
        self._content.refresh_list()
        self.show_all()
        self.show()
