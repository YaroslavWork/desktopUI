"""Hyprland monitor list and enable/disable via hyprctl keyword monitor."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def list_monitors() -> list[dict[str, Any]]:
    """Return active monitors from `hyprctl monitors -j` (disabled outputs are omitted)."""
    try:
        r = subprocess.run(
            ["hyprctl", "monitors", "-j"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return []
        data = json.loads(r.stdout)
        if isinstance(data, list):
            return [m for m in data if isinstance(m, dict)]
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        return []
    return []


def _enable_spec(m: dict[str, Any]) -> str:
    name = str(m.get("name", ""))
    w = int(m.get("width", 0))
    h = int(m.get("height", 0))
    rr = float(m.get("refreshRate", 60.0))
    x = int(m.get("x", 0))
    y = int(m.get("y", 0))
    scale = float(m.get("scale", 1.0))
    rrs = f"{rr:.6f}".rstrip("0").rstrip(".")
    if not rrs:
        rrs = "60"
    return f"{name},{w}x{h}@{rrs},{x}x{y},{scale}"


def set_monitor_enabled(m: dict[str, Any]) -> bool:
    spec = _enable_spec(m)
    try:
        r = subprocess.run(
            ["hyprctl", "keyword", "monitor", spec],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def set_monitor_disabled(name: str) -> bool:
    try:
        r = subprocess.run(
            ["hyprctl", "keyword", "monitor", f"{name},disable"],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def apply_single_active(monitors: list[dict[str, Any]], active_name: str) -> tuple[bool, str]:
    """Enable only `active_name`; disable all other listed monitors."""
    if not monitors:
        return False, "No monitors reported by Hyprland."
    names = {str(m.get("name", "")) for m in monitors}
    if active_name not in names:
        return False, "Unknown display."
    target = next(m for m in monitors if str(m.get("name", "")) == active_name)
    if not set_monitor_enabled(target):
        return False, "Failed to enable selected display."
    for m in monitors:
        n = str(m.get("name", ""))
        if n != active_name:
            set_monitor_disabled(n)
    return True, ""


def apply_all_enabled(monitors: list[dict[str, Any]]) -> tuple[bool, str]:
    """Enable every monitor with its current geometry."""
    if not monitors:
        return False, "No monitors."
    for m in monitors:
        if not set_monitor_enabled(m):
            return False, f"Failed to enable {m.get('name', '?')}."
    return True, ""


class DisplaysService:
    def list_monitors(self) -> list[dict[str, Any]]:
        return list_monitors()

    def apply_single_active(self, monitors: list[dict[str, Any]], active_name: str) -> tuple[bool, str]:
        return apply_single_active(monitors, active_name)

    def apply_all_enabled(self, monitors: list[dict[str, Any]]) -> tuple[bool, str]:
        return apply_all_enabled(monitors)


displays_service = DisplaysService()
