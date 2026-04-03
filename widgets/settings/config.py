"""Settings widget: popup with logout, block, shutdown buttons."""

import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_display_settings_opener: Callable[[], None] | None = None


def set_display_settings_opener(fn: Callable[[], None] | None) -> None:
    global _display_settings_opener
    _display_settings_opener = fn

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button

from services.wallpaper_service import wallpaper_service
from utils.assets import load_icon, logout_icon, lock_icon, power_icon


def _run(cmd: list[str]) -> None:
    """Run command in background."""
    try:
        subprocess.Popen(cmd, start_new_session=True)
    except Exception:
        pass


class SettingsBarContent(Box):
    """Settings popup content: logout, block, shutdown buttons with icons."""

    def __init__(self, **kwargs):
        wallpaper_img = load_icon("Video, Audio, Sound/Gallery Minimalistic.svg", 20)
        logout_img = logout_icon(20)
        lock_img = lock_icon(20)
        power_img = power_icon(20)

        wallpaper_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(200, 40),
        )
        wallpaper_btn.set_relief(Gtk.ReliefStyle.NONE)
        if wallpaper_img:
            wallpaper_btn.set_image(wallpaper_img)
            wallpaper_btn.set_always_show_image(True)
        wallpaper_btn.set_label("Change wallpaper")
        wallpaper_btn.connect("clicked", self._on_change_wallpaper)
        self._wallpaper_btn = wallpaper_btn

        logout_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(200, 40),
        )
        logout_btn.set_relief(Gtk.ReliefStyle.NONE)
        if logout_img:
            logout_btn.set_image(logout_img)
            logout_btn.set_always_show_image(True)
        logout_btn.set_label("Log out")
        logout_btn.connect("clicked", self._on_logout)
        self._logout_btn = logout_btn

        block_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(200, 40),
        )
        block_btn.set_relief(Gtk.ReliefStyle.NONE)
        if lock_img:
            block_btn.set_image(lock_img)
            block_btn.set_always_show_image(True)
        block_btn.set_label("Block")
        block_btn.connect("clicked", self._on_block)
        self._block_btn = block_btn

        shutdown_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(200, 40),
        )
        shutdown_btn.set_relief(Gtk.ReliefStyle.NONE)
        if power_img:
            shutdown_btn.set_image(power_img)
            shutdown_btn.set_always_show_image(True)
        shutdown_btn.set_label("Shutdown")
        shutdown_btn.connect("clicked", self._on_shutdown)
        self._shutdown_btn = shutdown_btn

        display_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(200, 40),
        )
        display_btn.set_relief(Gtk.ReliefStyle.NONE)
        display_btn.set_label("Display Settings")
        display_btn.connect("clicked", self._on_display_settings)
        self._display_btn = display_btn

        super().__init__(
            orientation="vertical",
            spacing=4,
            style_classes=["settings-widget"],
            children=[
                wallpaper_btn,
                display_btn,
                logout_btn,
                block_btn,
                shutdown_btn,
            ],
            **kwargs,
        )

    def refresh_tinted_icons(self) -> None:
        pairs = [
            (self._wallpaper_btn, load_icon("Video, Audio, Sound/Gallery Minimalistic.svg", 20)),
            (self._logout_btn, logout_icon(20)),
            (self._block_btn, lock_icon(20)),
            (self._shutdown_btn, power_icon(20)),
        ]
        for btn, img in pairs:
            if img:
                btn.set_image(img)
                btn.set_always_show_image(True)

    def _on_display_settings(self, _btn) -> None:
        if _display_settings_opener is not None:
            _display_settings_opener()

    def _on_change_wallpaper(self, _btn) -> None:
        ok, msg = wallpaper_service.apply_random()
        if not ok:
            _btn.set_tooltip_text(msg)
            return
        _btn.set_tooltip_text(f"Applied:\n{msg}")

    def _on_logout(self, _btn) -> None:
        _run(["hyprctl", "dispatch", "exit"])

    def _on_block(self, _btn) -> None:
        _run(["hyprlock"])

    def _on_shutdown(self, _btn) -> None:
        _run(["systemctl", "poweroff"])
