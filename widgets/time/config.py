import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

from services.weather_service import weather_service
from utils.assets import load_weather_icon
from utils.main_thread_debug import main_thread_span

POLL_MS = 1000
WEATHER_POLL_MS = 600_000
WEATHER_ICON_SIZE = 20


class TimeWidget(Button):
    """24h clock + weekday/date; wttr.in weather with secondary-colored icon and temperature."""

    def __init__(self, **kwargs):
        self._clock_label = Label(
            label="",
            style_classes=["time-widget-clock-line"],
        )
        self._clock_label.set_xalign(0.0)

        self._date_label = Label(
            label="",
            style_classes=["time-widget-date-line"],
        )
        self._date_label.set_xalign(0.0)

        time_stack = Box(
            orientation="vertical",
            spacing=1,
            style_classes=["time-widget-stack"],
            children=[self._clock_label, self._date_label],
        )
        time_stack.set_hexpand(False)

        self._weather_temp_label = Label(
            label="— °C",
            style_classes=["time-widget-weather-temp"],
        )
        self._weather_temp_label.set_xalign(0.0)

        self._last_weather_icon_rel = "Weather/Temperature.svg"
        self._weather_img = load_weather_icon(self._last_weather_icon_rel, WEATHER_ICON_SIZE)

        self._weather_row = Box(
            orientation="horizontal",
            spacing=6,
            style_classes=["time-widget-weather-row"],
        )
        self._weather_row.set_hexpand(False)
        self._weather_row.set_valign(Gtk.Align.CENTER)
        if self._weather_img is not None:
            self._weather_row.add(self._weather_img)
        self._weather_row.add(self._weather_temp_label)

        inner = Box(
            orientation="horizontal",
            spacing=13,
            style_classes=["time-widget-inner"],
            children=[
                time_stack,
                self._weather_row,
            ],
        )
        inner.set_hexpand(False)

        super().__init__(
            child=inner,
            style_classes=["time-widget", "flat"],
            v_align="center",
            **kwargs,
        )
        self.set_relief(Gtk.ReliefStyle.NONE)
        inner.set_halign(Gtk.Align.CENTER)

        invoke_repeater(POLL_MS, self._tick_clock)
        invoke_repeater(WEATHER_POLL_MS, self._tick_weather)
        GLib.idle_add(self._weather_idle_bootstrap)

        self._tick_clock()

    def _weather_idle_bootstrap(self) -> bool:
        weather_service.refresh()
        self._apply_weather_snapshot()
        return False

    def _tick_clock(self) -> bool:
        self._clock_label.set_label(time.strftime("%H:%M:%S"))
        t = time.localtime()
        self._date_label.set_label(time.strftime("%A, %B ", t) + str(t.tm_mday))
        return True

    def _tick_weather(self) -> bool:
        weather_service.refresh()
        self._apply_weather_snapshot()
        return True

    def _apply_weather_snapshot(self) -> None:
        with main_thread_span("weather widget apply (labels + icon)"):
            snap = weather_service.snapshot()
            rel = str(snap.get("icon_rel") or "Weather/Temperature.svg")
            self._last_weather_icon_rel = rel

            temp = snap.get("temp_c")
            if temp is not None and snap.get("ok"):
                self._weather_temp_label.set_label(f"{float(temp):.0f}°C")
            else:
                self._weather_temp_label.set_label("— °C")

            if self._weather_img is not None:
                try:
                    self._weather_row.remove(self._weather_img)
                except Exception:
                    pass
                self._weather_img = None

            new_img = load_weather_icon(rel, WEATHER_ICON_SIZE)
            self._weather_img = new_img
            if new_img is not None:
                self._weather_row.pack_start(new_img, False, False, 0)
                self._weather_row.reorder_child(new_img, 0)
            self._weather_row.show_all()

    def refresh_tinted_icons(self) -> None:
        with main_thread_span("weather icon reload (theme)"):
            rel = self._last_weather_icon_rel
            if self._weather_img is not None:
                try:
                    self._weather_row.remove(self._weather_img)
                except Exception:
                    pass
                self._weather_img = None
            self._weather_img = load_weather_icon(rel, WEATHER_ICON_SIZE)
            if self._weather_img is not None:
                self._weather_row.pack_start(self._weather_img, False, False, 0)
                self._weather_row.reorder_child(self._weather_img, 0)
            self._weather_row.show_all()
