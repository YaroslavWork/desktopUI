"""Register callbacks to hot-reload Fabric GTK stylesheets (e.g. after matugen updates colors.css)."""

from __future__ import annotations

from collections.abc import Callable

_stylesheet_reloaders: list[Callable[[], None]] = []
_icon_reloaders: list[Callable[[], None]] = []


def register_stylesheet_reload(fn: Callable[[], None]) -> None:
    _stylesheet_reloaders.append(fn)


def register_icon_reload(fn: Callable[[], None]) -> None:
    """Run after stylesheet reload; re-tint SVG icons from updated colors.css."""
    _icon_reloaders.append(fn)


def reload_stylesheets() -> None:
    for fn in _stylesheet_reloaders:
        try:
            fn()
        except Exception:
            pass
    for fn in _icon_reloaders:
        try:
            fn()
        except Exception:
            pass
