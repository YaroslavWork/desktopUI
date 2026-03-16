"""Widget showing Hyprland workspaces as rounded buttons with planet initials."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.utils.helpers import invoke_repeater

from services.workspaces_service import workspaces_service
from services.workspace_apps_service import workspace_apps_service


# Initials: Sun, Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune
WORKSPACE_INITIALS = ["Su", "Me", "V", "E", "Ma", "J", "Sa", "U", "N"]

WORKSPACE_EVENTS = ("workspace", "workspacev2")
WINDOW_EVENTS = ("openwindow", "closewindow", "movewindow", "movewindowv2")


class WorkspacesWidget(Box):
    """Shows 9 workspaces as rounded buttons with initials. Active uses primary color."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=8,
            style_classes=["workspaces-widget"],
            **kwargs,
        )
        self._buttons: list[tuple[int, Button]] = []
        self._connect_hyprland_events()
        self._build_buttons()
        self._update_active()
        self._update_occupied()

    def _connect_hyprland_events(self):
        """Connect to Hyprland workspace events."""
        try:
            from fabric.hyprland import Hyprland

            self._hyprland = Hyprland(commands_only=False)
            for evt in WORKSPACE_EVENTS + WINDOW_EVENTS:
                self._hyprland.connect(f"event::{evt}", self._on_hyprland_event)
        except Exception:
            self._hyprland = None
            invoke_repeater(1000, self._update_all)

    def _update_all(self, *_args):
        self._update_active()
        self._update_occupied()

    def _on_hyprland_event(self, _event):
        self._update_active()
        self._update_occupied()

    def _update_occupied(self):
        """Add/remove occupied class when workspace has apps."""
        with_apps = workspace_apps_service.get_workspace_ids_with_apps()
        for ws_id, btn in self._buttons:
            ctx = btn.get_style_context()
            if ws_id in with_apps:
                ctx.add_class("occupied")
            else:
                ctx.remove_class("occupied")

    def _build_buttons(self):
        """Create rounded buttons with initials (always visible)."""
        for ws_id, label in enumerate(WORKSPACE_INITIALS, start=1):
            btn = Button(
                label=label,
                style_classes=["workspace-button", "flat"],
                size=(32, 32),
                v_align="center",
            )
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_tooltip_text(f"Workspace {ws_id}")
            btn.connect("clicked", self._on_workspace_clicked, ws_id)
            self._buttons.append((ws_id, btn))
            self.add(btn)

    def _on_workspace_clicked(self, _btn, ws_id: int):
        workspaces_service.switch_to_workspace(ws_id)

    def _update_active(self):
        """Update active state styling."""
        active = workspaces_service.get_active_workspace_id()
        for ws_id, btn in self._buttons:
            ctx = btn.get_style_context()
            if ws_id == active:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")
