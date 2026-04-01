import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

from utils.assets import clock_icon


class TimeWidget(Button):
    """Time widget that cycles through formats on click: hh:mm:ss -> dd.mm.yyyy -> [weekday] Week x."""

    FORMATS = (
        "%H:%M:%S",      # Time hh:mm:ss
        "%d.%m.%Y",      # Date dd.mm.yyyy
        "Week %V: %A",    # Day of week + ISO week number
    )

    def __init__(self, **kwargs):
        self._time_label = Label(label="", style_classes=["time-widget-label"])
        clock_img = clock_icon(18)
        if clock_img is not None:
            content = Box(
                orientation="horizontal",
                spacing=6,
                children=[clock_img, self._time_label],
                style_classes=["time-widget-content"],
            )
        else:
            content = self._time_label
        super().__init__(
            child=content,
            style_classes=["time-widget", "flat"],
            v_align="center",
            **kwargs,
        )
        self.set_relief(Gtk.ReliefStyle.NONE)
        content.set_halign(Gtk.Align.CENTER)
        content.set_hexpand(False)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self._current_index = 0
        self._repeater_id = invoke_repeater(1000, self._update)
        self.connect("button-press-event", self._on_press)
        self.connect("scroll-event", self._on_scroll)
        self._update()

    def refresh_tinted_icons(self) -> None:
        child = self.get_child()
        if child is None:
            return
        ch = child.get_children()
        if len(ch) < 2:
            return
        first = ch[0]
        child.remove(first)
        img = clock_icon(18)
        if img:
            child.pack_start(img, False, False, 0)
            child.reorder_child(img, 0)
        child.show_all()

    def _update(self) -> bool:
        self._time_label.set_label(time.strftime(self.FORMATS[self._current_index]))
        return True

    def _cycle_next(self):
        self._current_index = (self._current_index + 1) % len(self.FORMATS)
        self._update()

    def _cycle_prev(self):
        self._current_index = (self._current_index - 1) % len(self.FORMATS)
        self._update()

    def _on_press(self, _widget, event):
        if event.button == 1:
            self._cycle_next()
        elif event.button == 3:
            self._cycle_prev()

    def _on_scroll(self, _widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self._cycle_next()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self._cycle_prev()
