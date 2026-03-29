"""Battery widget: pill-shaped level bar with percentage on the right."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

BAR_WIDTH = 96
BAR_HEIGHT = 8
UPDATE_MS = 5000


def _battery_sysfs_dir() -> Path | None:
    root = Path("/sys/class/power_supply")
    if not root.is_dir():
        return None
    for name in sorted(p.name for p in root.iterdir()):
        if name.startswith("BAT"):
            base = root / name
            if (base / "capacity").exists():
                return base
    return None


def _read_battery() -> tuple[int | None, str | None]:
    base = _battery_sysfs_dir()
    if base is None:
        return None, None
    cap: int | None = None
    try:
        cap = int((base / "capacity").read_text().strip())
        cap = max(0, min(100, cap))
    except (ValueError, OSError):
        pass
    status: str | None = None
    try:
        status = (base / "status").read_text().strip().lower()
    except OSError:
        pass
    return cap, status


class BatteryWidget(Box):
    """Horizontal pill bar (rounded ends) plus percentage label."""

    def __init__(self, **kwargs):
        self._fill = Box(style_classes=["battery-fill"])
        self._fill.set_size_request(0, BAR_HEIGHT)
        self._fill.set_hexpand(False)
        self._fill.set_halign(Gtk.Align.START)

        self._track = Box(
            orientation="horizontal",
            spacing=0,
            style_classes=["battery-track"],
            children=[self._fill],
        )
        self._track.set_size_request(BAR_WIDTH, BAR_HEIGHT)

        self._label = Label(label="—", style_classes=["battery-percent-label"])

        super().__init__(
            orientation="horizontal",
            spacing=8,
            style_classes=["battery-widget"],
            children=[self._track, self._label],
            **kwargs,
        )
        self.set_valign(Gtk.Align.CENTER)
        invoke_repeater(UPDATE_MS, self._update)
        self._update()

    def _update(self) -> bool:
        cap, status = _read_battery()
        ctx = self.get_style_context()
        if cap is None:
            self._label.set_label("—")
            self._fill.set_size_request(0, BAR_HEIGHT)
            ctx.remove_class("battery-charging")
            ctx.remove_class("battery-low")
            return True

        self._label.set_label(f"{cap}%")
        w = max(0, min(BAR_WIDTH, int(round(BAR_WIDTH * cap / 100))))
        self._fill.set_size_request(w, BAR_HEIGHT)

        if status == "charging":
            ctx.add_class("battery-charging")
        else:
            ctx.remove_class("battery-charging")
        if cap <= 20:
            ctx.add_class("battery-low")
        else:
            ctx.remove_class("battery-low")
        return True
