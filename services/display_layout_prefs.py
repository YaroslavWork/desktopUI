"""Persist Layout display mode; applied on desktopUI startup so Hyprland.conf needs no monitor= lines."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _state_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / "desktopUI"
    d.mkdir(parents=True, exist_ok=True)
    return d / "display_layout.json"


def save_all_displays_mode() -> None:
    _write_json({"mode": "all"})


def save_single_display(output: str) -> None:
    _write_json({"mode": "single", "output": output})


def _write_json(data: dict[str, Any]) -> None:
    try:
        _state_path().write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def load_prefs() -> dict[str, Any] | None:
    path = _state_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def persist_hypr_monitors_conf_for_prefs(p: dict[str, Any]) -> None:
    """Rewrite ~/.config/hypr/desktopui-displays.conf from saved mode (for hyprctl reload)."""
    from services.hypr_display_state import write_desktopui_displays_conf

    mode = str(p.get("mode") or "").lower()
    if mode == "single" and p.get("output"):
        write_desktopui_displays_conf("single", str(p["output"]).strip())
    elif mode == "all":
        write_desktopui_displays_conf("all", None)


def apply_saved_layout_at_startup() -> None:
    """Re-apply last Display Settings choice after Hyprland/session start."""
    p = load_prefs()
    if not p:
        return
    from services.displays_service import apply_all_enabled, apply_single_active

    ok = False
    mode = p.get("mode")
    if mode == "single" and p.get("output"):
        ok, _ = apply_single_active(str(p["output"]).strip())
    elif mode == "all":
        ok, _ = apply_all_enabled()
    if ok:
        persist_hypr_monitors_conf_for_prefs(p)
