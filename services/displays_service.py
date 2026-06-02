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


def list_monitors_all() -> list[dict[str, Any]]:
    """All outputs from ``hyprctl monitors all -j`` (includes disabled; needed to turn eDP-1 off)."""
    try:
        r = subprocess.run(
            ["hyprctl", "monitors", "all", "-j"],
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


def format_monitor_enable_spec(m: dict[str, Any]) -> str:
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
    spec = format_monitor_enable_spec(m)
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


def primary_output_name() -> str | None:
    """
    Hyprland "primary" output: focused enabled head, else first enabled, else first listed connector.
    """
    all_mons = list_monitors_all()
    names = {str(m.get("name", "")).strip() for m in all_mons if m.get("name")}
    if not names:
        return None
    active = list_monitors()
    for m in active:
        n = str(m.get("name", "")).strip()
        if n in names and m.get("focused"):
            return n
    for m in active:
        n = str(m.get("name", "")).strip()
        if n in names:
            return n
    for m in all_mons:
        n = str(m.get("name", "")).strip()
        if n in names:
            return n
    return None


def apply_single_active(active_name: str) -> tuple[bool, str]:
    """Enable only `active_name`; disable every other output Hyprland knows about."""
    all_mons = list_monitors_all()
    if not all_mons:
        return False, "No monitors reported by Hyprland."
    names = {str(m.get("name", "")).strip() for m in all_mons if m.get("name")}
    if active_name not in names:
        return False, "Unknown display."
    target = next(m for m in all_mons if str(m.get("name", "")).strip() == active_name)
    if not set_monitor_enabled(target):
        return False, "Failed to enable selected display."
    for m in all_mons:
        n = str(m.get("name", "")).strip()
        if n and n != active_name:
            set_monitor_disabled(n)
    return True, ""


def apply_all_enabled() -> tuple[bool, str]:
    """Enable every output using geometry from ``monitors all``."""
    all_mons = list_monitors_all()
    if not all_mons:
        return False, "No monitors."
    for m in all_mons:
        if not set_monitor_enabled(m):
            return False, f"Failed to enable {m.get('name', '?')}."
    return True, ""


class DisplaysService:
    def list_monitors(self) -> list[dict[str, Any]]:
        return list_monitors()

    def list_monitors_all(self) -> list[dict[str, Any]]:
        return list_monitors_all()

    def primary_output_name(self) -> str | None:
        return primary_output_name()

    def apply_single_active(self, active_name: str) -> tuple[bool, str]:
        return apply_single_active(active_name)

    def apply_all_enabled(self) -> tuple[bool, str]:
        return apply_all_enabled()


displays_service = DisplaysService()
