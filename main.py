#!/usr/bin/env python3
"""Main entry point: runs all widgets and services together."""

import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Initialize services (side effect on import)
from services.user_service import user_service  # noqa: F401

from fabric import Application
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.datetime import DateTime
from fabric.widgets.wayland import WaylandWindow

from widgets.user.config import UserBarContent


class MainBar(WaylandWindow):
    """Combined status bar: user info (left) + clock (right)."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            **kwargs,
        )
        self.children = CenterBox(
            start_children=UserBarContent(),
            end_children=DateTime(),
        )


if __name__ == "__main__":
    app = Application("desktop-ui", MainBar())
    app.run()
