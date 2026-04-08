"""Hyprland keyboard layout: short label (e.g. PL, US) from main keyboard device JSON."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def _fetch_devices() -> dict[str, Any] | None:
    try:
        r = subprocess.run(
            ["hyprctl", "devices", "-j"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        data = json.loads(r.stdout)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _token_to_label(token: str) -> str:
    t = (token or "").strip().lower()
    if not t:
        return "?"
    if "(" in t:
        t = t.split("(")[0].strip()
    if not t:
        return "?"
    if len(t) <= 3:
        return t.upper()
    return t[:2].upper()


def _keymap_to_label(active_keymap: str | None) -> str:
    if not active_keymap or not str(active_keymap).strip():
        return "?"
    low = str(active_keymap).lower()
    hints: tuple[tuple[str, str], ...] = (
        ("ukrainian", "UA"),
        ("polish", "PL"),
        ("english (us)", "US"),
        ("english(us)", "US"),
        ("english (uk)", "GB"),
        ("english(uk)", "GB"),
        ("russian", "RU"),
        ("german", "DE"),
        ("french", "FR"),
        ("spanish", "ES"),
        ("italian", "IT"),
        ("japanese", "JP"),
        ("english", "US"),
    )
    for needle, short in hints:
        if needle in low:
            return short
    return _token_to_label(active_keymap.split()[0] if active_keymap else "?")


def snapshot() -> tuple[str, str | None]:
    """Return ``(short_label, fingerprint)`` for change detection.

    ``fingerprint`` is ``None`` if Hyprland data could not be read.
    """
    data = _fetch_devices()
    if not data:
        return "—", None

    main_kb: dict[str, Any] | None = None
    for k in data.get("keyboards") or []:
        if not isinstance(k, dict):
            continue
        if k.get("main"):
            main_kb = k
            break

    if main_kb is None:
        for k in data.get("keyboards") or []:
            if isinstance(k, dict) and k.get("name") == "at-translated-set-2-keyboard":
                main_kb = k
                break
    if main_kb is None:
        for k in data.get("keyboards") or []:
            if isinstance(k, dict):
                main_kb = k
                break

    if main_kb is None:
        return "—", None

    layout_raw = str(main_kb.get("layout") or "").strip()
    variant_raw = str(main_kb.get("variant") or "")
    try:
        idx = int(main_kb.get("active_layout_index", 0))
    except (TypeError, ValueError):
        idx = 0

    parts = [p.strip() for p in layout_raw.split(",") if p.strip()]
    variants = [p.strip() for p in variant_raw.split(",")]
    label: str
    if parts and 0 <= idx < len(parts):
        label = _token_to_label(parts[idx])
    elif parts:
        label = _token_to_label(parts[0])
    else:
        label = _keymap_to_label(main_kb.get("active_keymap") if isinstance(main_kb.get("active_keymap"), str) else None)

    var = variants[idx] if variants and 0 <= idx < len(variants) else ""
    fp = f"{idx}|{layout_raw}|{variant_raw}|{main_kb.get('active_keymap', '')}|{var}"
    return label, fp
