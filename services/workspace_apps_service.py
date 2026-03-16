"""Service for getting open apps in current Hyprland workspace."""

import json
import subprocess
from dataclasses import dataclass
from fabric.core.service import Service


@dataclass
class WorkspaceApp:
    address: str
    app_class: str
    title: str


class WorkspaceAppsService(Service):
    """Provides list of open apps in the current Hyprland workspace."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._apps: list[WorkspaceApp] = []

    def get_apps(self) -> list[WorkspaceApp]:
        """Fetch and return apps in current workspace."""
        try:
            active = subprocess.run(
                ["hyprctl", "-j", "activeworkspace"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if active.returncode != 0:
                return []
            ws_data = json.loads(active.stdout)
            ws_id = ws_data.get("id")

            clients = subprocess.run(
                ["hyprctl", "-j", "clients"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if clients.returncode != 0:
                return []
            clients_data = json.loads(clients.stdout)

            self._apps = [
                WorkspaceApp(
                    address=str(c.get("address", "")),
                    app_class=c.get("class", "?"),
                    title=c.get("title", ""),
                )
                for c in clients_data
                if isinstance(c.get("workspace"), dict)
                and c["workspace"].get("id") == ws_id
                and c.get("mapped", True)
            ]
            return self._apps
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []


workspace_apps_service = WorkspaceAppsService()
