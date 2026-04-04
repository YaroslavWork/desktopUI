from __future__ import annotations

from typing import Any

from fabric import Service


class SingletonService(Service):
    """Base service class with singleton pattern and common functionality.

    Each concrete subclass gets its own single instance. A shared class-level
    ``_instance`` would incorrectly reuse one object across subclasses.
    """

    _instances: dict[type[Any], SingletonService] = {}

    def __new__(cls, *args: Any, **kwargs: Any) -> SingletonService:
        if cls not in SingletonService._instances:
            SingletonService._instances[cls] = super().__new__(cls)
        return SingletonService._instances[cls]

    def __init__(self, **kwargs):
        if hasattr(self, "_initialized"):
            return
        super().__init__(**kwargs)
        self._initialized = True