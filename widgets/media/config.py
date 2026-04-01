"""Media controls: MPRIS prev / play-pause / next, title, volume scroll, raise & player cycle."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk, Pango

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.image import Image as CoverImage
from fabric.widgets.label import Label
from fabric.utils.helpers import invoke_repeater

from services.mpris_service import mpris_service
from utils.album_art import load_album_art_pixbuf
from utils.assets import pause_icon, play_icon, skip_next_icon, skip_prev_icon

POLL_MS = 1200
BTN = 28
ICON_SZ = 16
ART_W = 56
ART_H = 38
VOLUME_STEP = 0.06


def _icon_button(svg_fn, tooltip: str) -> Button:
    img = svg_fn(ICON_SZ)
    btn = Button(
        style_classes=["media-control-button", "flat"],
        size=(BTN, BTN),
        v_align="center",
    )
    btn.set_relief(Gtk.ReliefStyle.NONE)
    if img:
        btn.set_image(img)
        btn.set_always_show_image(True)
    btn.set_tooltip_text(tooltip)
    return btn


class MediaControlsWidget(Box):
    """MPRIS transport + cover; multiple players = clickable source tabs, each controlled separately."""

    def __init__(self, **kwargs):
        self._prev_btn = _icon_button(skip_prev_icon, "Previous track")
        self._prev_btn.connect("clicked", lambda *_: (mpris_service.previous_track(), self.refresh()))

        self._play_btn = _icon_button(play_icon, "Play / Pause")
        self._play_btn.connect("clicked", lambda *_: (mpris_service.play_pause(), self.refresh()))

        self._next_btn = _icon_button(skip_next_icon, "Next track")
        self._next_btn.connect("clicked", lambda *_: (mpris_service.next_track(), self.refresh()))

        self._title = Label(
            label="",
            style_classes=["media-title-label"],
        )
        self._title.set_ellipsize(Pango.EllipsizeMode.END)
        self._title.set_max_width_chars(24)
        self._title.set_xalign(0.0)
        self._title.set_hexpand(False)

        self._cover = CoverImage(
            size=(ART_W, ART_H),
            style_classes=["media-album-art"],
            v_align="center",
            h_align="center",
            icon_name="audio-x-generic",
            icon_size=20,
        )
        self._cover.set_hexpand(False)
        self._art_url_loaded: str | None = None

        self._sources_row = Box(
            orientation="horizontal",
            spacing=4,
            style_classes=["media-sources-row"],
        )
        self._sources_row.set_hexpand(False)
        self._sources_row.set_valign(Gtk.Align.CENTER)
        self._sources_row_key: tuple[tuple[str, str | None], ...] | None = None

        super().__init__(
            orientation="horizontal",
            spacing=6,
            style_classes=["media-controls-widget"],
            children=[
                self._sources_row,
                self._cover,
                self._prev_btn,
                self._play_btn,
                self._next_btn,
                self._title,
            ],
            **kwargs,
        )
        self.set_valign(Gtk.Align.CENTER)
        self.set_tooltip_text(
            "Media (MPRIS)\n\n"
            "Scroll: volume (selected source) · Right-click: focus player\n"
            "Middle-click: cycle source · With several apps: click a tab to control that source"
        )
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("scroll-event", self._on_scroll)
        self.connect("button-press-event", self._on_press)

        self._last_playing: bool | None = None

        invoke_repeater(POLL_MS, self._poll)
        self.refresh()

    def _set_cover_from_url(self, url: str | None) -> None:
        if url == self._art_url_loaded:
            return
        if not url:
            self._art_url_loaded = None
            self._cover.clear()
            self._cover.set_from_icon_name("audio-x-generic", 20)
            return
        pb = load_album_art_pixbuf(url, ART_W, ART_H)
        self._art_url_loaded = url
        if pb:
            self._cover.set_from_pixbuf(pb)
        else:
            self._cover.clear()
            self._cover.set_from_icon_name("audio-x-generic", 20)

    def _on_scroll(self, _w, event: Gdk.EventScroll) -> bool:
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            return False
        delta = VOLUME_STEP if event.direction == Gdk.ScrollDirection.UP else (
            -VOLUME_STEP if event.direction == Gdk.ScrollDirection.DOWN else 0.0
        )
        if delta == 0.0:
            return False
        nv = mpris_service.set_volume_delta(delta)
        if nv is not None:
            self.refresh()
            return True
        return False

    def _on_press(self, _w, event: Gdk.EventButton) -> bool:
        if event.button == 3:
            mpris_service.raise_player()
            self.refresh()
            return True
        if event.button == 2:
            mpris_service.cycle_player()
            self.refresh()
            return True
        return False

    def _on_source_picked(self, _btn: Button, dest: str) -> None:
        mpris_service.select_player(dest)
        self.refresh()

    def _sync_sources_row(self, overview: list, active_dest: str | None) -> None:
        if len(overview) <= 1:
            self._sources_row_key = None
            for w in self._sources_row.get_children():
                self._sources_row.remove(w)
            self._sources_row.set_visible(False)
            return

        row_key = tuple(
            (str(info["player"]), info.get("status") if isinstance(info.get("status"), str) else None)
            for info in overview
        )
        self._sources_row.set_visible(True)

        if row_key == self._sources_row_key and self._sources_row.get_children():
            for i, child in enumerate(self._sources_row.get_children()):
                ctx = child.get_style_context()
                dest = overview[i]["player"]
                if dest == active_dest:
                    ctx.add_class("active")
                else:
                    ctx.remove_class("active")
            return

        self._sources_row_key = row_key
        for w in self._sources_row.get_children():
            self._sources_row.remove(w)

        for info in overview:
            dest = info["player"]
            lab = info.get("label_short") or info.get("label") or dest
            tip = f"{info.get('label', dest)}\n{info.get('status') or '?'}"
            pill = Button(
                label=lab,
                style_classes=["media-source-pill", "flat"],
                v_align="center",
            )
            pill.set_relief(Gtk.ReliefStyle.NONE)
            pill.set_tooltip_text(tip)
            if dest == active_dest:
                pill.get_style_context().add_class("active")
            pill.connect("clicked", self._on_source_picked, dest)
            self._sources_row.add(pill)
        self._sources_row.show_all()

    def _poll(self) -> bool:
        self.refresh()
        return True

    def refresh(self) -> None:
        snap = mpris_service.get_snapshot()
        status = snap.get("status")
        title = (snap.get("title") or "").strip()
        artist = (snap.get("artist") or "").strip()
        vol = snap.get("volume")

        if not snap.get("player"):
            self._title.set_label("—")
            self._set_cover_from_url(None)
            self._sync_sources_row([], None)
            self.get_style_context().add_class("media-idle")
            self.set_tooltip_text(snap.get("tooltip") or "")
            self._last_playing = None
            self._set_play_icon(False)
            return

        self._sync_sources_row(mpris_service.get_players_overview(), snap.get("player"))

        self.get_style_context().remove_class("media-idle")
        self._set_cover_from_url(snap.get("art_url"))

        line = title if title else "Unknown title"
        if artist and title:
            line = f"{title} · {artist}"
        elif artist:
            line = artist
        self._title.set_label(line)

        tip = snap.get("tooltip") or ""
        if isinstance(vol, float):
            tip = f"{tip}\nVolume: {int(round(vol * 100))}%"
        self.set_tooltip_text(tip)

        playing = status == "Playing"
        self._set_play_icon(playing)

    def _set_play_icon(self, playing: bool) -> None:
        if self._last_playing == playing:
            return
        self._last_playing = playing
        img = pause_icon(ICON_SZ) if playing else play_icon(ICON_SZ)
        if img:
            self._play_btn.set_image(img)
            self._play_btn.set_always_show_image(True)
