"""Middle-click (wheel press) → single primary display: Hyprland exec, optional hyprctl bind, or bar click."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_path() -> None:
    root = str(_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def switch_to_primary_display_only() -> tuple[bool, str]:
    """
    Enable only the primary (focused, else first) output; disable others.
    Persists the same way as Display Settings → single output.
    """
    _ensure_path()
    from services.display_layout_prefs import (
        persist_hypr_monitors_conf_for_prefs,
        save_single_display,
    )
    from services.displays_service import apply_single_active, primary_output_name

    name = primary_output_name()
    if not name:
        return False, "No output found."
    ok, msg = apply_single_active(name)
    if not ok:
        return ok, msg or "hyprctl failed."
    save_single_display(name)
    persist_hypr_monitors_conf_for_prefs({"mode": "single", "output": name})
    return True, name


def register_hypr_bind_for_primary_display() -> bool:
    """
    Register a global Hyprland bind: middle mouse → primary display only.

    Uses ``DESKTOPUI_PRIMARY_MOUSE_CODE`` (default ``274``, Linux ``BTN_MIDDLE``).
    Run ``wev`` and press the wheel to pick another code if needed.

    Unbinds the same key first, then binds ``exec`` to ``bin/desktopui-primary-display``
    (no commas in the path segment Hyprland parses as the exec target).
    """
    code = int(os.environ.get("DESKTOPUI_PRIMARY_MOUSE_CODE", "274").strip() or "274")
    launcher = _project_root() / "bin" / "desktopui-primary-display"
    if not launcher.is_file():
        return False
    cmd = str(launcher.resolve())
    batch = f"keyword unbind ,mouse:{code}; keyword bind ,mouse:{code},exec,{cmd}"
    try:
        r = subprocess.run(
            ["hyprctl", "--batch", batch],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main() -> int:
    ok, out = switch_to_primary_display_only()
    if ok:
        return 0
    sys.stderr.write(f"desktopUI primary display: {out}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
