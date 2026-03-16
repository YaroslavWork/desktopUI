"""Service for Hyprland workspaces: active workspace and switching."""

import json
import subprocess
from fabric.core.service import Service


class WorkspacesService(Service):
    """Provides active Hyprland workspace and workspace switching."""

    def get_active_workspace_id(self) -> int:
        """Return the current active workspace ID (1-9)."""
        try:
            result = subprocess.run(
                ["hyprctl", "-j", "activeworkspace"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode != 0:
                return 1
            data = json.loads(result.stdout)
            ws_id = data.get("id", 1)
            return int(ws_id) if isinstance(ws_id, (int, float)) else 1
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return 1

    def switch_to_workspace(self, workspace_id: int) -> None:
        """Switch to the given workspace (1-9)."""
        try:
            subprocess.run(
                ["hyprctl", "dispatch", "workspace", str(workspace_id)],
                capture_output=True,
                timeout=1,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass


workspaces_service = WorkspacesService()
