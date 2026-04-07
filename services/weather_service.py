"""Weather via wttr.in (JSON). Set DESKTOPUI_WEATHER_LOCATION (e.g. London) or leave unset for auto IP."""

from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from utils.main_thread_debug import main_thread_span

# WMO-style codes from wttr.in (WorldWeatherOnline). Checked top-down.
_THUNDER = {200, 386, 389, 392, 395}
_SNOW = {
    179, 227, 230, 323, 326, 329, 332, 335, 338, 368, 371, 374, 377, 350, 320,
}
_RAIN = {
    176, 263, 266, 281, 284, 293, 296, 299, 302, 305, 308, 311, 314, 317, 356, 359, 353,
}
_FOG = {143, 248, 260}
_CLOUD = {119, 122}
_PARTLY = {116}
_CLEAR = {113}

_DEFAULT_ICON = "Weather/Temperature.svg"


def _is_night_local() -> bool:
    h = time.localtime().tm_hour
    return h < 7 or h >= 20


def _icon_for_code(code: int) -> str:
    night = _is_night_local()
    if code in _THUNDER:
        return "Weather/Cloud Storm.svg"
    if code in _SNOW:
        return "Weather/Cloud Snowfall.svg"
    if code in _RAIN:
        return "Weather/Cloud Rain.svg"
    if code in _FOG:
        return "Weather/Fog.svg"
    if code in _CLOUD:
        return "Weather/Clouds.svg"
    if code in _PARTLY:
        return "Weather/Cloudy Moon.svg" if night else "Weather/Cloud Sun.svg"
    if code in _CLEAR:
        return "Weather/Moon Stars.svg" if night else "Weather/Sun.svg"
    return "Weather/Cloud.svg"


class WeatherService:
    """Cached snapshot for the time/weather widget."""

    def __init__(self) -> None:
        self._icon_rel: str = _DEFAULT_ICON
        self._temp_c: float | None = None
        self._ok: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "icon_rel": self._icon_rel,
            "temp_c": self._temp_c,
            "ok": self._ok,
        }

    def refresh(self) -> None:
        with main_thread_span("weather refresh (wttr.in)"):
            loc = os.environ.get("DESKTOPUI_WEATHER_LOCATION", "").strip()
            path = f"/{urllib.parse.quote(loc)}" if loc else "/"
            url = f"https://wttr.in{path}?format=j1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "desktopUI/1.0 (weather; +https://github.com/chubin/wttr.in)"},
            )
            ctx = ssl.create_default_context()
            try:
                with urllib.request.urlopen(req, timeout=14, context=ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
                self._ok = False
                return

            try:
                cc = data["current_condition"][0]
                raw_code = cc.get("weatherCode", "0")
                code = int(raw_code) if str(raw_code).isdigit() else 0
                t_raw = cc.get("temp_C", "")
                temp: float | None = None
                if t_raw is not None and str(t_raw).strip() != "":
                    temp = float(str(t_raw).replace(",", "."))
            except (KeyError, IndexError, TypeError, ValueError):
                self._ok = False
                return

            self._icon_rel = _icon_for_code(code)
            self._temp_c = temp
            self._ok = True


weather_service = WeatherService()
