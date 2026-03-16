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
    app = Application("desktop-ui", MainBar())
    app.set_stylesheet_from_file(str(PROJECT_ROOT / "style.css"))
    app.run()
