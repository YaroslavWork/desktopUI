"""Widget showing open apps in current workspace with icon or first letter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.utils.helpers import invoke_repeater

from services.workspace_apps_service import workspace_apps_service, WorkspaceApp


def _get_app_display(app: WorkspaceApp) -> tuple[str | None, str]:
    """Return (icon_name or None, fallback_letter)."""
    icon_name = app.app_class.lower().replace(" ", "-")
    return (icon_name, (app.app_class or "?")[0].upper())


# Events that should trigger workspace apps refresh
WORKSPACE_REFRESH_EVENTS = (
    "workspace", "workspacev2", "openwindow", "closewindow",
    "movewindow", "movewindowv2", "activewindow", "activewindowv2",
)


class WorkspaceAppsWidget(Box):
    """Shows open apps in current workspace as icon or first letter buttons."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=4,
            style_classes=["workspace-apps-widget"],
            **kwargs,
        )
        self._buttons: list[tuple[WorkspaceApp, Button]] = []
        self._connect_hyprland_events()
        self._update()

    def _connect_hyprland_events(self):
        """Connect to Hyprland events for workspace/window changes."""
        try:
            from fabric.hyprland import Hyprland

            self._hyprland = Hyprland(commands_only=False)
            for evt in WORKSPACE_REFRESH_EVENTS:
                self._hyprland.connect(f"event::{evt}", self._on_hyprland_event)
        except Exception:
            self._hyprland = None
            invoke_repeater(2000, self._update)  # Fallback: poll when Hyprland unavailable

    def _on_hyprland_event(self, _event):
        self._update()

    def _clear_buttons(self):
        for _app, btn in self._buttons:
            self.remove(btn)
        self._buttons.clear()

    def _create_app_button(self, app: WorkspaceApp) -> Button:
        icon_name, letter = _get_app_display(app)
        try:
            theme = Gtk.IconTheme.get_default()
            if theme.has_icon(icon_name):
                img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
                btn = Button(
                    child=img,
                    style_classes=["workspace-app-button", "flat"],
                    size=(28, 28),
                    v_align="center",
                )
            else:
                btn = Button(
                    label=letter,
                    style_classes=["workspace-app-button", "workspace-app-letter", "flat"],
                    size=(28, 28),
                    v_align="center",
                )
        except Exception:
            btn = Button(
                label=letter,
                style_classes=["workspace-app-button", "workspace-app-letter", "flat"],
                size=(28, 28),
                v_align="center",
            )
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(app.title or app.app_class)
        btn.connect("clicked", self._on_app_clicked, app)
        return btn

    def _on_app_clicked(self, _btn, app: WorkspaceApp):
        import subprocess
        try:
            subprocess.run(
                ["hyprctl", "dispatch", "focuswindow", f"address:{app.address}"],
                capture_output=True,
                timeout=1,
            )
        except Exception:
            pass

    def _update(self) -> bool:
        apps = workspace_apps_service.get_apps()
        current = [(a.address, a.app_class) for a in apps]
        if hasattr(self, "_last_apps") and self._last_apps == current:
            self._update_active_glow()
            return True
        self._last_apps = current

        self._clear_buttons()
        for app in apps:
            btn = self._create_app_button(app)
            self._buttons.append((app, btn))
            self.add(btn)
        self.show_all()
        self._update_active_glow()
        return True

    def _update_active_glow(self):
        """Add glow to the active/focused window's button."""
        active_addr = workspace_apps_service.get_active_window_address()
        for app, btn in self._buttons:
            ctx = btn.get_style_context()
            if app.address == active_addr:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")
