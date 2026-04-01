"""Register callbacks to hot-reload Fabric GTK stylesheets (e.g. after matugen updates colors.css)."""

from __future__ import annotations

from collections.abc import Callable

_reloaders: list[Callable[[], None]] = []


def register_stylesheet_reload(fn: Callable[[], None]) -> None:
    _reloaders.append(fn)


def reload_stylesheets() -> None:
    for fn in _reloaders:
        try:
            fn()
        except Exception:
            pass
