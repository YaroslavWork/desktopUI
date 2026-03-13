import fabric
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.window import Window
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.wayland import WaylandWindow as Window


class StatusBar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            layer="top",  # Ensure it stays above other apps
            anchor="left top right",  # Anchors the bar at the top, stretching from left to right
            exclusivity="auto",  # Reserves space for the bar so it behaves like a normal window
            **kwargs
        )

        self.date_time = DateTime()
        self.children = CenterBox(center_children=self.date_time)

if __name__ == "__main__":
    bar = StatusBar()
    app = Application("bar-example", bar)
    app.run()