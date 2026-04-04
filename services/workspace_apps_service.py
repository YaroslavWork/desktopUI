"""Service for getting open apps per Hyprland workspace."""

import json
import subprocess
from dataclasses import dataclass

from fabric.core.service import Service


@dataclass
class WorkspaceApp:
    address: str
    app_class: str
    title: str


def _client_workspace_id(c: dict) -> int | None:
    if not c.get("mapped", True):
        return None
    ws = c.get("workspace")
    if isinstance(ws, dict):
        wid = ws.get("id")
    elif isinstance(ws, int):
        wid = ws
    else:
        return None
    if wid is None:
        return None
    try:
        i = int(wid)
    except (TypeError, ValueError):
        return None
    if 1 <= i <= 9:
        return i
    return None


class WorkspaceAppsService(Service):
    """Provides open windows grouped by workspace (1–9) and helpers for the active workspace."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_apps_by_workspace(self) -> dict[int, list[WorkspaceApp]]:
        """All mapped windows on workspaces 1–9, keyed by workspace id."""
        empty = {i: [] for i in range(1, 10)}
        try:
            clients = subprocess.run(
                ["hyprctl", "-j", "clients"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if clients.returncode != 0:
                return empty
            clients_data = json.loads(clients.stdout)
            result: dict[int, list[WorkspaceApp]] = {i: [] for i in range(1, 10)}
            for c in clients_data:
                wid = _client_workspace_id(c)
                if wid is None:
                    continue
                result[wid].append(
                    WorkspaceApp(
                        address=str(c.get("address", "")),
                        app_class=c.get("class", "?"),
                        title=c.get("title", ""),
                    )
                )
            return result
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return empty

    def _get_active_workspace_id(self) -> int | None:
        try:
            active = subprocess.run(
                ["hyprctl", "-j", "activeworkspace"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if active.returncode != 0:
                return None
            ws_id = json.loads(active.stdout).get("id")
            return int(ws_id) if ws_id is not None else None
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return None

    def get_apps(self) -> list[WorkspaceApp]:
        """Windows on the currently active workspace."""
        by_ws = self.get_apps_by_workspace()
        aid = self._get_active_workspace_id()
        if aid is None or aid not in by_ws:
            return []
        return by_ws[aid]

    def get_workspace_ids_with_apps(self) -> set[int]:
        """Workspace IDs (1–9) that have at least one mapped window."""
        by_ws = self.get_apps_by_workspace()
        return {wid for wid, apps in by_ws.items() if apps}

    def get_active_window_address(self) -> str | None:
        """Return address of the currently focused window."""
        try:
            result = subprocess.run(
                ["hyprctl", "-j", "activewindow"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout)
            addr = data.get("address")
            return str(addr) if addr is not None else None
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None


workspace_apps_service = WorkspaceAppsService()
