#!/usr/bin/env python3
"""Main entry point: runs all widgets and services together."""

import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize services (side effect on import)
from services.user_service import user_service  # noqa: F401

from fabric import Application
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.wayland import WaylandWindow

from widgets.user.config import UserBarContent


class MainBar(WaylandWindow):
    """Bar taking full top width with user info on left, transparent elsewhere."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            **kwargs,
        )
        self.children = CenterBox(start_children=UserBarContent())


if __name__ == "__main__":
    import re
    from fabric.utils.helpers import compile_css

    app = Application("desktop-ui", MainBar())
    css = (PROJECT_ROOT / "style.css").read_text()
    compiled = compile_css(css, base_path=str(PROJECT_ROOT))
    compiled = re.sub(r":root\s*\{([^}]*)\}", lambda m: m.group(1).strip(), compiled, flags=re.DOTALL)
    app.set_stylesheet_from_string(compiled, compile=False)
    app.run()
