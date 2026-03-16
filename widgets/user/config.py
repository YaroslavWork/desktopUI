import sys
from pathlib import Path

# Ensure project root is in path when run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.window import Window
from fabric.utils.helpers import invoke_repeater

from services.user_service import user_service
from utils.assets import user_icon


def _format_session(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class UserBarContent(Box):
    """Reusable user info widget: Welcome message + session time."""

    def __init__(self, **kwargs):
        self._welcome_label = Label(
            label=f"Welcome, {user_service.username}.",
            style_classes=["user-welcome"],
        )
        self._session_label = Label(
            label="Current session: 00:00:00",
            style_classes=["user-session"],
        )
        user_img = user_icon(32)
        if user_img is not None:
            header = Box(
                orientation="horizontal",
                spacing=12,
                children=[user_img, self._welcome_label],
                style_classes=["user-widget-header"],
            )
            children = [header, self._session_label]
        else:
            children = [self._welcome_label, self._session_label]
        super().__init__(
            orientation="vertical",
            spacing=8,
            children=children,
            style_classes=["user-widget"],
            **kwargs,
        )
        self._update_session()
        invoke_repeater(1000, self._update_session)

    def _update_session(self) -> bool:
        seconds = user_service.refresh_session_seconds()
        self._session_label.set_label(f"Current session: {_format_session(seconds)}")
        return True


class UserBar(Window):
    """Standalone window with user info."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = UserBarContent()
