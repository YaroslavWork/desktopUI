#!/usr/bin/env python3
"""Main entry point: runs all widgets and services together."""

import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize services (side effect on import)
from services.user_service import user_service  # noqa: F401
from services.workspaces_service import workspaces_service  # noqa: F401
from services.theme_service import register_icon_reload, register_stylesheet_reload  # noqa: F401

from fabric import Application

from modules.config import (
    UserModuleBar,
    UserPopup,
    SettingsPopup,
    settings_widget,
    user_widget,
    wifi_widget,
)
from widgets.display_settings.config import DisplaySettingsPopup
from widgets.settings.config import set_display_settings_opener
from utils.css_compile import compile_desktop_ui_stylesheet


if __name__ == "__main__":
    bar = UserModuleBar()
    user_popup = UserPopup()
    user_popup.hide()
    settings_popup = SettingsPopup()
    settings_popup.hide()
    display_settings_popup = DisplaySettingsPopup()
    display_settings_popup.hide()

    app = Application("desktop-ui", bar)
    app.add_window(user_popup)
    app.add_window(settings_popup)
    app.add_window(display_settings_popup)
    app._user_popup = user_popup
    app._settings_popup = settings_popup
    app._display_settings_popup = display_settings_popup

    def _open_display_settings() -> None:
        settings_popup.hide()
        display_settings_popup.open_centered()

    set_display_settings_opener(_open_display_settings)

    compiled = compile_desktop_ui_stylesheet(PROJECT_ROOT)
    app.set_stylesheet_from_string(compiled, compile=False)

    register_stylesheet_reload(
        lambda: app.set_stylesheet_from_string(
            compile_desktop_ui_stylesheet(PROJECT_ROOT),
            compile=False,
        )
    )

    register_icon_reload(bar.refresh_tinted_icons)
    register_icon_reload(user_widget.refresh_tinted_icons)
    register_icon_reload(settings_widget.refresh_tinted_icons)
    register_icon_reload(wifi_widget.refresh_tinted_icons)

    app.run()
