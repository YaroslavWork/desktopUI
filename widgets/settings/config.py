"""Settings widget: popup with logout, block, shutdown buttons."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button

from utils.assets import logout_icon, lock_icon, power_icon


def _run(cmd: list[str]) -> None:
    """Run command in background."""
    try:
        subprocess.Popen(cmd, start_new_session=True)
    except Exception:
        pass


class SettingsBarContent(Box):
    """Settings popup content: logout, block, shutdown buttons with icons."""

    def __init__(self, **kwargs):
        logout_img = logout_icon(20)
        lock_img = lock_icon(20)
        power_img = power_icon(20)

        logout_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(120, 40),
        )
        logout_btn.set_relief(Gtk.ReliefStyle.NONE)
        if logout_img:
            logout_btn.set_image(logout_img)
            logout_btn.set_always_show_image(True)
        logout_btn.set_label("Log out")
        logout_btn.connect("clicked", self._on_logout)

        block_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(120, 40),
        )
        block_btn.set_relief(Gtk.ReliefStyle.NONE)
        if lock_img:
            block_btn.set_image(lock_img)
            block_btn.set_always_show_image(True)
        block_btn.set_label("Block")
        block_btn.connect("clicked", self._on_block)

        shutdown_btn = Button(
            style_classes=["settings-action-button", "flat"],
            size=(120, 40),
        )
        shutdown_btn.set_relief(Gtk.ReliefStyle.NONE)
        if power_img:
            shutdown_btn.set_image(power_img)
            shutdown_btn.set_always_show_image(True)
        shutdown_btn.set_label("Shutdown")
        shutdown_btn.connect("clicked", self._on_shutdown)

        super().__init__(
            orientation="vertical",
            spacing=4,
            style_classes=["settings-widget"],
            children=[logout_btn, block_btn, shutdown_btn],
            **kwargs,
        )

    def _on_logout(self, _btn) -> None:
        _run(["hyprctl", "dispatch", "exit"])

    def _on_block(self, _btn) -> None:
        _run(["hyprlock"])

    def _on_shutdown(self, _btn) -> None:
        _run(["systemctl", "poweroff"])
