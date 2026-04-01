"""Compile desktopUI style.css (Fabric + strip :root for GTK provider)."""

from __future__ import annotations

import re
from pathlib import Path

from fabric.utils.helpers import compile_css


def compile_desktop_ui_stylesheet(project_root: Path) -> str:
    css = (project_root / "style.css").read_text()
    compiled = compile_css(css, base_path=str(project_root))
    return re.sub(
        r":root\s*\{([^}]*)\}",
        lambda m: m.group(1).strip(),
        compiled,
        flags=re.DOTALL,
    )
