import sys
from pathlib import Path

# Ensure project root is in path when run from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fabric.widgets.centerbox import CenterBox
from fabric.widgets.wayland import WaylandWindow

from services.user_service import user_service  # noqa: F401
from widgets.user.config import UserBarContent


# User widget with fixed width (left side of bar)
USER_WIDGET_WIDTH = 220
user_widget = UserBarContent(size=(USER_WIDGET_WIDTH, -1))


class UserModuleBar(WaylandWindow):
    """Bar taking full top width with user widget on left, transparent elsewhere."""

    def __init__(self, **kwargs):
        super().__init__(
            layer="top",
            anchor="left top right",
            exclusivity="auto",
            **kwargs,
        )
        self.children = CenterBox(start_children=user_widget)


if __name__ == "__main__":
    from fabric import Application

    app = Application("user-module-bar", UserModuleBar())
    app.set_stylesheet_from_file(str(PROJECT_ROOT / "style.css"))
    app.run()
