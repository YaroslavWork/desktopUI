"""Wi-Fi bar module: icon-only when disconnected; SSID + throughput when connected. Click opens nmtui in a terminal."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

from services.wifi_service import WiFiLinkState, wifi_service
from utils.assets import load_icon

POLL_MS = 2000
ICON_SIZE = 24
ICON_ONLY_SIZE = 40
ICON_WIFI = "Network, IT, Programming/Wi-Fi Router Minimalistic.svg"


def _wifi_icon(size: int = ICON_SIZE) -> Gtk.Image | None:
    """Tint with ``--secondary`` from ``colors.css`` (matches weather-style accent)."""
    img = load_icon(ICON_WIFI, size, primary=False)
    if img is not None:
        img.set_size_request(size, size)
        img.set_halign(Gtk.Align.CENTER)
        img.set_valign(Gtk.Align.CENTER)
    return img

_TERMINAL_TRIES: tuple[list[str], ...] = (
    ["foot", "nmtui"],
    ["alacritty", "-e", "nmtui"],
    ["kitty", "nmtui"],
    ["wezterm", "start", "--", "nmtui"],
    ["konsole", "-e", "nmtui"],
    ["gnome-terminal", "--", "nmtui"],
    ["xterm", "-e", "nmtui"],
)


def spawn_nmtui() -> bool:
    """Run ``nmtui`` inside a terminal. Returns True if a launcher was started."""
    custom = (os.environ.get("DESKTOPUI_TERMINAL") or "").strip()
    if custom:
        try:
            parts = shlex.split(custom)
            if parts:
                subprocess.Popen([*parts, "nmtui"], start_new_session=True)
                return True
        except (OSError, ValueError):
            pass

    for argv in _TERMINAL_TRIES:
        if shutil.which(argv[0]):
            try:
                subprocess.Popen(argv, start_new_session=True)
                return True
            except OSError:
                continue

    term = (os.environ.get("TERMINAL") or "").strip()
    if term:
        try:
            parts = shlex.split(term)
            if parts:
                subprocess.Popen([*parts, "nmtui"], start_new_session=True)
                return True
        except (OSError, ValueError):
            pass
    return False


def _fmt_bytes_per_sec(bps: float) -> str:
    if bps < 1:
        return "0 B/s"
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps / 1024 / 1024:.1f} MB/s"


def _status_line(st: WiFiLinkState) -> str:
    if not st.nmcli_ok:
        return st.error or "Wi-Fi unavailable"
    if not st.radio_on:
        return "Radio off"
    if not st.device:
        return "No adapter"
    if st.state == "connected":
        if st.ssid:
            sig = f" · {st.signal}%" if st.signal is not None else ""
            return f"{st.ssid}{sig}"
        return "Connected"
    if st.state == "unavailable":
        return "Unavailable"
    return "Disconnected"


class WiFiWidget(Button):
    """Disconnected: icon only. Connected: icon + SSID and rates. Click → ``nmtui`` in a terminal."""

    def __init__(self, **kwargs):
        self._wifi_img = _wifi_icon()
        self._ssid_l = Label(
            label="Wi‑Fi",
            style_classes=["wifi-widget-ssid"],
        )
        self._ssid_l.set_xalign(0.0)

        self._down_l = Label(
            label="↓ —",
            style_classes=["wifi-widget-rate"],
        )
        self._down_l.set_xalign(0.0)
        self._up_l = Label(
            label="↑ —",
            style_classes=["wifi-widget-rate"],
        )
        self._up_l.set_xalign(0.0)

        self._text_col = Box(
            orientation="vertical",
            spacing=1,
            style_classes=["wifi-widget-text-col"],
            children=[self._ssid_l, self._down_l, self._up_l],
        )

        self._wifi_row = Box(
            orientation="horizontal",
            spacing=8,
            style_classes=["wifi-widget-inner"],
            children=([self._wifi_img] if self._wifi_img else []) + [self._text_col],
        )
        self._wifi_row.set_valign(Gtk.Align.CENTER)

        super().__init__(
            child=self._wifi_row,
            style_classes=["wifi-widget", "flat"],
            v_align="center",
            **kwargs,
        )
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_tooltip_text("NetworkManager: open nmtui (manage connections)")
        self.connect("clicked", self._on_clicked)

        invoke_repeater(POLL_MS, self._tick)
        self._last_connected = False
        self._tick()

    def _on_clicked(self, *_args) -> None:
        if not spawn_nmtui():
            self.set_tooltip_text("Could not open a terminal for nmtui. Set DESKTOPUI_TERMINAL or TERMINAL.")
        else:
            self.set_tooltip_text("NetworkManager: open nmtui (manage connections)")

    def _tick(self) -> bool:
        st, rx_bps, tx_bps = wifi_service.poll_with_throughput()
        connected = st.state == "connected"
        self._last_connected = connected
        if connected:
            self._text_col.show()
            self._ssid_l.set_label(_status_line(st))
            self._down_l.set_label(f"↓ {_fmt_bytes_per_sec(rx_bps)}")
            self._up_l.set_label(f"↑ {_fmt_bytes_per_sec(tx_bps)}")
            self.set_size_request(-1, -1)
        else:
            self._text_col.hide()
            self.set_size_request(ICON_ONLY_SIZE, ICON_ONLY_SIZE)

        ctx = self.get_style_context()
        if connected:
            ctx.remove_class("wifi-widget-idle")
        else:
            ctx.add_class("wifi-widget-idle")
        return True

    def _apply_compact_layout(self) -> None:
        """Keep icon-only vs expanded layout after GTK show_all() from icon refresh."""
        if self._last_connected:
            self._text_col.show()
            self.set_size_request(-1, -1)
        else:
            self._text_col.hide()
            self.set_size_request(ICON_ONLY_SIZE, ICON_ONLY_SIZE)

    def refresh_tinted_icons(self) -> None:
        if self._wifi_img is not None:
            try:
                self._wifi_row.remove(self._wifi_img)
            except Exception:
                pass
            self._wifi_img = None
        self._wifi_img = _wifi_icon()
        if self._wifi_img is not None:
            self._wifi_row.pack_start(self._wifi_img, False, False, 0)
            self._wifi_row.reorder_child(self._wifi_img, 0)
            self._wifi_row.show_all()
            self._apply_compact_layout()
