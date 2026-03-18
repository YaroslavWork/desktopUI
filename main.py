#!/usr/bin/env python3
"""Main entry point: runs all widgets and services together."""

import re
import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize services (side effect on import)
from services.user_service import user_service  # noqa: F401
from services.workspaces_service import workspaces_service  # noqa: F401

from fabric import Application
from fabric.utils.helpers import compile_css

from modules.config import UserModuleBar, UserPopup, SettingsPopup


if __name__ == "__main__":
    bar = UserModuleBar()
    user_popup = UserPopup()
    user_popup.hide()
    settings_popup = SettingsPopup()
    settings_popup.hide()

    app = Application("desktop-ui", bar)
    app.add_window(user_popup)
    app.add_window(settings_popup)
    app._user_popup = user_popup
    app._settings_popup = settings_popup

    css = (PROJECT_ROOT / "style.css").read_text()
    compiled = compile_css(css, base_path=str(PROJECT_ROOT))
    compiled = re.sub(r":root\s*\{([^}]*)\}", lambda m: m.group(1).strip(), compiled, flags=re.DOTALL)
    app.set_stylesheet_from_string(compiled, compile=False)
    app.run()
