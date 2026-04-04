"""Hyprland workspaces: each column is workspace initial + app icons for that workspace."""

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
from services.workspace_apps_service import workspace_apps_service, WorkspaceApp
from widgets.workspace_apps.config import build_workspace_app_button, set_app_button_active

# Initials: Sun, Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune
WORKSPACE_INITIALS = ["Su", "Me", "V", "E", "Ma", "J", "Sa", "U", "N"]

WORKSPACE_EVENTS = ("workspace", "workspacev2")
WINDOW_EVENTS = ("openwindow", "closewindow", "movewindow", "movewindowv2")


def _apps_key(apps: list[WorkspaceApp]) -> tuple[tuple[str, str], ...]:
    return tuple((a.address, a.app_class) for a in apps)


class WorkspacesWidget(Box):
    """Nine columns: workspace switcher + windows on that workspace (icons / letters)."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=6,
            style_classes=["workspaces-widget"],
            **kwargs,
        )
        self._columns: list[tuple[int, Button, Box, Box]] = []
        self._last_keys: dict[int, tuple[tuple[str, str], ...]] = {}
        self._connect_hyprland_events()
        self._build_columns()
        self._sync_all()

    def _connect_hyprland_events(self) -> None:
        try:
            from fabric.hyprland import Hyprland

            self._hyprland = Hyprland(commands_only=False)
            for evt in WORKSPACE_EVENTS + WINDOW_EVENTS + (
                "activewindow",
                "activewindowv2",
            ):
                self._hyprland.connect(f"event::{evt}", self._on_hyprland_event)
        except Exception:
            self._hyprland = None
            invoke_repeater(1000, self._poll_fallback)

    def _poll_fallback(self, *_args) -> bool:
        self._sync_all()
        return True

    def _on_hyprland_event(self, _event) -> None:
        self._sync_all()

    def _build_columns(self) -> None:
        for ws_id, label in enumerate(WORKSPACE_INITIALS, start=1):
            ws_btn = Button(
                label=label,
                style_classes=["workspace-button", "flat"],
                size=(32, 32),
                v_align="center",
            )
            ws_btn.set_relief(Gtk.ReliefStyle.NONE)
            ws_btn.set_tooltip_text(f"Workspace {ws_id}")
            ws_btn.connect("clicked", self._on_workspace_clicked, ws_id)

            apps_row = Box(
                orientation="horizontal",
                spacing=2,
                style_classes=["workspace-column-apps"],
            )
            apps_row.set_valign(Gtk.Align.CENTER)

            col = Box(
                orientation="horizontal",
                spacing=4,
                style_classes=["workspace-column"],
                children=[ws_btn, apps_row],
            )
            col.set_valign(Gtk.Align.CENTER)
            self._columns.append((ws_id, ws_btn, apps_row, col))
            self.add(col)

    def _on_workspace_clicked(self, _btn, ws_id: int) -> None:
        workspaces_service.switch_to_workspace(ws_id)

    def _fill_app_row(self, apps_row: Box, apps: list[WorkspaceApp], active_addr: str | None) -> None:
        for w in apps_row.get_children():
            apps_row.remove(w)
        for app in apps:
            btn = build_workspace_app_button(app)
            addr = getattr(btn, "_desktopui_app_address", None)
            set_app_button_active(btn, addr is not None and addr == active_addr)
            apps_row.add(btn)
        apps_row.show_all()

    def _apply_app_row_active(self, apps_row: Box, active_addr: str | None) -> None:
        for child in apps_row.get_children():
            addr = getattr(child, "_desktopui_app_address", None)
            if addr is None:
                continue
            set_app_button_active(child, addr == active_addr)

    def _sync_all(self) -> None:
        by_ws = workspace_apps_service.get_apps_by_workspace()
        active_ws = workspaces_service.get_active_workspace_id()
        active_addr = workspace_apps_service.get_active_window_address()

        for ws_id, ws_btn, apps_row, col in self._columns:
            apps = by_ws.get(ws_id, [])
            key = _apps_key(apps)

            col_ctx = col.get_style_context()
            if apps:
                col_ctx.add_class("workspace-column-occupied")
            else:
                col_ctx.remove_class("workspace-column-occupied")

            ctx = ws_btn.get_style_context()
            if ws_id == active_ws:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")
            if apps:
                ctx.add_class("occupied")
            else:
                ctx.remove_class("occupied")

            last = self._last_keys.get(ws_id)
            if last != key:
                self._last_keys[ws_id] = key
                self._fill_app_row(apps_row, apps, active_addr)
            else:
                self._apply_app_row_active(apps_row, active_addr)

    def refresh_tinted_icons(self) -> None:
        self._last_keys.clear()
        self._sync_all()
