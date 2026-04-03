import sys
from pathlib import Path

gi = __import__("gi")
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Ensure project root is in path when run from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.wayland import WaylandWindow

from services.user_service import user_service  # noqa: F401
from services.workspace_apps_service import workspace_apps_service  # noqa: F401
from services.mpris_service import mpris_service  # noqa: F401
from services.wallpaper_service import wallpaper_service  # noqa: F401
from services.weather_service import weather_service  # noqa: F401
from widgets.user.config import UserBarContent
from widgets.time.config import TimeWidget
from widgets.workspace_apps.config import WorkspaceAppsWidget
from widgets.workspaces.config import WorkspacesWidget
from widgets.settings.config import SettingsBarContent
from widgets.battery.config import BatteryWidget
from widgets.media.config import MediaControlsWidget
from utils.assets import settings_icon


# User widget with fixed width (for popup)
USER_WIDGET_WIDTH = 220
user_widget = UserBarContent(size=(USER_WIDGET_WIDTH, -1))

# Settings widget for popup
settings_widget = SettingsBarContent(size=(220, -1))

# Popup: user widget overlay below the bar
USER_POPUP_MARGIN_TOP = 4  # Below bar


class UserPopup(WaylandWindow):
    """User widget overlay in top-left corner, below the bar."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="left top",
            margin=f"{USER_POPUP_MARGIN_TOP}px 0 0 4px",
            exclusivity="none",
            style_classes=["user-popup"],
            **kwargs,
        )
        self.children = Box(children=[user_widget])
        self.hide()


class SettingsPopup(WaylandWindow):
    """Settings widget overlay in top-right corner, below the bar."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            anchor="right top",
            margin=f"{USER_POPUP_MARGIN_TOP}px 4px 0 0",
            exclusivity="none",
            style_classes=["user-popup", "settings-popup"],
            **kwargs,
        )
        self.children = Box(children=[settings_widget])
        self.hide()


class UserModuleBar(WaylandWindow):
    """Bar taking full top width with user letter button on left."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            margin="12px 12px 12px 12px",
            exclusivity="auto",
            style_classes=["top-bar"],
            **kwargs,
        )
        user_letter = (user_service.username or "?")[0].upper()
        user_button = Button(
            label=user_letter,
            style_classes=["user-letter-button", "flat"],
            size=(40, 40),
            v_align="center",
        )
        user_button.set_relief(Gtk.ReliefStyle.NONE)
        user_button.connect("clicked", self._on_galaxy_clicked)

        time_widget = TimeWidget(size=(280, -1))
        workspaces_widget = WorkspacesWidget()
        workspace_apps_widget = WorkspaceAppsWidget()
        media_widget = MediaControlsWidget()

        battery_widget = BatteryWidget()
        settings_img = settings_icon(22)
        settings_button = Button(
            style_classes=["settings-bar-button", "flat"],
            size=(40, 40),
            v_align="center",
        )
        settings_button.set_relief(Gtk.ReliefStyle.NONE)
        if settings_img:
            settings_button.set_image(settings_img)
            settings_button.set_always_show_image(True)
        else:
            settings_button.set_label("⚙")
        settings_button.connect("clicked", self._on_settings_clicked)

        self._time_widget = time_widget
        self._workspace_apps_widget = workspace_apps_widget
        self._media_widget = media_widget
        self._settings_button = settings_button

        # Left bar: user, time, active apps, media
        left_bar = Box(
            orientation="horizontal",
            spacing=12,
            style_classes=["bar-section", "bar-section-left"],
            children=[user_button, time_widget, workspace_apps_widget, media_widget],
        )
        # Center bar: workspaces
        center_bar = Box(
            orientation="horizontal",
            spacing=8,
            style_classes=["bar-section", "bar-section-center"],
            children=[workspaces_widget],
        )
        # Right bar: battery, then settings
        right_bar = Box(
            orientation="horizontal",
            spacing=12,
            style_classes=["bar-section", "bar-section-right"],
            children=[battery_widget, settings_button],
        )

        self.children = CenterBox(
            start_children=[left_bar],
            center_children=[center_bar],
            end_children=[right_bar],
            spacing=8,
            style_classes=["top-bar"],
        )

    def refresh_tinted_icons(self) -> None:
        img = settings_icon(22)
        if img:
            self._settings_button.set_image(img)
            self._settings_button.set_always_show_image(True)
        self._time_widget.refresh_tinted_icons()
        self._workspace_apps_widget.refresh_tinted_icons()
        self._media_widget.refresh_tinted_icons()

    def _on_settings_clicked(self, _button):
        app = self.get_application()
        if app and hasattr(app, "_settings_popup"):
            popup = app._settings_popup
            if popup.get_visible():
                popup.hide()
            else:
                popup.show_all()

    def _on_galaxy_clicked(self, _button):
        app = self.get_application()
        if app and hasattr(app, "_user_popup"):
            popup = app._user_popup
            if popup.get_visible():
                popup.hide()
            else:
                popup.show_all()


if __name__ == "__main__":
    from fabric import Application

    from utils.css_compile import compile_desktop_ui_stylesheet

    bar = UserModuleBar()
    popup = UserPopup()
    popup.hide()

    app = Application("user-module-bar", bar)
    app.add_window(popup)
    app._user_popup = popup
    app.set_stylesheet_from_string(
        compile_desktop_ui_stylesheet(PROJECT_ROOT),
        compile=False,
    )
    app.run()
