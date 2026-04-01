"""Battery widget: pill-shaped level bar with percentage on the right."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

BAR_WIDTH = 96
BAR_HEIGHT = 8
UPDATE_MS = 5000
ANIM_MS = 320
FRAME_MS = 14


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


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


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

        self._anim_source_id: int | None = None
        self._anim_mode: str | None = None
        self._anim_progress = 0.0
        self._anim_cap = 0
        self._initialized = False

        invoke_repeater(UPDATE_MS, self._update)
        self._update()

    def _cancel_anim(self) -> None:
        if self._anim_source_id is not None:
            GLib.source_remove(self._anim_source_id)
            self._anim_source_id = None
        self._anim_mode = None

    def _apply_status_classes(self, ctx, cap: int, status: str | None) -> None:
        if status == "charging":
            ctx.add_class("battery-charging")
        else:
            ctx.remove_class("battery-charging")
        if cap <= 20:
            ctx.add_class("battery-low")
        else:
            ctx.remove_class("battery-low")

    def _set_bar_geometry(self, track_w: float, cap: int) -> None:
        tw = int(max(0, round(track_w)))
        self._track.set_size_request(tw, BAR_HEIGHT)
        fw = max(0, min(tw, int(round(tw * cap / 100)))) if tw > 0 else 0
        self._fill.set_size_request(fw, BAR_HEIGHT)
        frac = (tw / BAR_WIDTH) if BAR_WIDTH else 0.0
        self._label.set_opacity(min(1.0, max(0.0, frac)))
        if tw < 6:
            self._label.hide()
        else:
            self._label.show()

    def _sync_bar(self, cap: int) -> None:
        self._label.set_label(f"{cap}%")
        self._label.set_opacity(1.0)
        self._label.show()
        self._set_bar_geometry(float(BAR_WIDTH), cap)

    def _prepare_hidden(self) -> None:
        self._label.hide()
        self._label.set_opacity(0.0)
        self._track.set_size_request(0, BAR_HEIGHT)
        self._fill.set_size_request(0, BAR_HEIGHT)

    def _start_expand(self, cap: int) -> None:
        self._cancel_anim()
        self._anim_mode = "expand"
        self._anim_progress = 0.0
        self._anim_cap = cap
        self._label.set_label(f"{cap}%")
        self.show_all()
        self._set_bar_geometry(0.0, cap)

        def tick() -> bool:
            if self._anim_mode != "expand":
                return False
            self._anim_progress += FRAME_MS / ANIM_MS
            if self._anim_progress >= 1.0:
                self._anim_source_id = None
                self._anim_mode = None
                self._sync_bar(self._anim_cap)
                return False
            t = _smoothstep(self._anim_progress)
            self._set_bar_geometry(BAR_WIDTH * t, self._anim_cap)
            self._label.set_label(f"{self._anim_cap}%")
            return True

        self._anim_source_id = GLib.timeout_add(FRAME_MS, tick)

    def _start_collapse(self, cap: int) -> None:
        self._cancel_anim()
        self._anim_mode = "collapse"
        self._anim_progress = 0.0
        self._anim_cap = cap
        self._sync_bar(cap)

        def tick() -> bool:
            if self._anim_mode != "collapse":
                return False
            self._anim_progress += FRAME_MS / ANIM_MS
            if self._anim_progress >= 1.0:
                self._set_bar_geometry(0.0, self._anim_cap)
                self._anim_source_id = None
                self._anim_mode = None
                self.hide()
                return False
            t = _smoothstep(self._anim_progress)
            self._set_bar_geometry(BAR_WIDTH * (1.0 - t), self._anim_cap)
            self._label.set_label(f"{self._anim_cap}%")
            return True

        self._anim_source_id = GLib.timeout_add(FRAME_MS, tick)

    def _update(self) -> bool:
        cap, status = _read_battery()
        ctx = self.get_style_context()

        if cap is None:
            self._cancel_anim()
            if not self.get_visible():
                self.show_all()
            self._label.set_label("—")
            self._label.show()
            self._label.set_opacity(1.0)
            self._track.set_size_request(BAR_WIDTH, BAR_HEIGHT)
            self._fill.set_size_request(0, BAR_HEIGHT)
            ctx.remove_class("battery-charging")
            ctx.remove_class("battery-low")
            self._initialized = True
            return True

        self._apply_status_classes(ctx, cap, status)
        want_show = cap <= 95
        visible = self.get_visible()

        if self._anim_source_id is not None:
            if want_show and self._anim_mode == "collapse":
                self._cancel_anim()
                self.show_all()
                self._sync_bar(cap)
                return True
            if not want_show and self._anim_mode == "expand":
                self._cancel_anim()
                self._start_collapse(cap)
                return True

        if not self._initialized:
            self._initialized = True
            if want_show:
                self.show_all()
                self._sync_bar(cap)
            else:
                self._prepare_hidden()
                self.hide()
            return True

        if want_show and not visible and self._anim_source_id is None:
            self._start_expand(cap)
            return True

        if not want_show and visible and self._anim_source_id is None:
            self._start_collapse(cap)
            return True

        if want_show and visible and self._anim_source_id is None:
            self._sync_bar(cap)
        return True
