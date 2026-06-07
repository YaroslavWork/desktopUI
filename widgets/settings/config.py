"""Settings widget: popup with logout, block, shutdown buttons."""

import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label

from services.wallpaper_service import wallpaper_service
from services.displays_service import displays_service
from utils.assets import load_icon, logout_icon, lock_icon, power_icon


def _run(cmd: list[str]) -> None:
    """Run command in background."""
    try:
        subprocess.Popen(cmd, start_new_session=True)
    except Exception:
        pass


class SettingsBarContent(Box):
    """Settings popup content: logout, block, shutdown buttons and dynamic displays."""

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

        # Displays Section Header
        self._displays_header = Label(
            label="Displays",
            style_classes=["settings-displays-header"],
        )
        self._displays_header.set_xalign(0.0)

        # Displays Container
        self._displays_box = Box(
            orientation="vertical",
            spacing=4,
            style_classes=["settings-displays-container"],
        )

        super().__init__(
            orientation="vertical",
            spacing=4,
            style_classes=["settings-widget"],
            children=[
                wallpaper_btn,
                logout_btn,
                block_btn,
                shutdown_btn,
                self._displays_header,
                self._displays_box,
            ],
            **kwargs,
        )

        # Connect displays service monitors-changed signal for reactive updates
        displays_service.connect("monitors-changed", lambda *_: self.refresh_displays())
        self.refresh_displays()

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

    def refresh_displays(self) -> None:
        """Dynamically populate display list with enable/disable actions."""
        # Clear old rows
        for child in self._displays_box.get_children():
            self._displays_box.remove(child)

        all_monitors = displays_service.list_monitors_all()
        active_monitors = displays_service.list_monitors()
        active_names = {m.get("name") for m in active_monitors if m.get("name")}

        if not all_monitors:
            no_display_lbl = Label(
                label="No displays detected",
                style_classes=["display-label"],
            )
            self._displays_box.add(no_display_lbl)
            self._displays_box.show_all()
            return

        for m in all_monitors:
            name = m.get("name", "Unknown")
            w = m.get("width", 0)
            h = m.get("height", 0)
            rr = m.get("refreshRate", 0.0)
            is_active = name in active_names

            # Row wrapper
            row = Box(
                orientation="horizontal",
                spacing=8,
                style_classes=["display-row", "display-row-active" if is_active else "display-row-inactive"],
            )

            # Left side: Display info (name + resolution)
            info_lbl = Label(
                label=f"{name} ({w}x{h} @ {rr:.1f}Hz)" if w and h else name,
                style_classes=["display-label"],
            )
            info_lbl.set_xalign(0.0)
            info_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END

            # Right side: Toggle button
            toggle_lbl = "Enabled" if is_active else "Disabled"
            toggle_btn = Button(
                label=toggle_lbl,
                style_classes=["display-toggle-btn", "flat"] if is_active else ["display-toggle-btn", "inactive", "flat"],
                size=(70, 24),
            )
            toggle_btn.set_relief(Gtk.ReliefStyle.NONE)
            toggle_btn.connect("clicked", lambda _, n=name, a=is_active: self._on_toggle_display(n, a))

            row.pack_start(info_lbl, True, True, 0)
            row.pack_end(toggle_btn, False, False, 0)

            self._displays_box.add(row)

        self._displays_box.show_all()

    def _on_toggle_display(self, name: str, is_active: bool) -> None:
        displays_service.toggle_monitor(name, not is_active)
        self.refresh_displays()
        # Schedule a delayed refresh to guarantee state is settled in hyprctl
        GLib.timeout_add(500, lambda: (self.refresh_displays(), False)[1])

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

