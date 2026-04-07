"""Opt-in stderr timing for work that runs on the GTK main thread.

Set environment variable ``DESKTOPUI_DEBUG_BLOCKING=1`` (or ``true`` / ``yes``).
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from typing import Generator


def blocking_debug_enabled() -> bool:
    v = (os.environ.get("DESKTOPUI_DEBUG_BLOCKING") or "").strip().lower()
    return v in ("1", "true", "yes")


@contextmanager
def main_thread_span(label: str) -> Generator[None, None, None]:
    if not blocking_debug_enabled():
        yield
        return
    print(f"[desktopUI] {label} START", file=sys.stderr, flush=True)
    t0 = time.monotonic()
    try:
        yield
    finally:
        ms = (time.monotonic() - t0) * 1000
        print(f"[desktopUI] {label} FINISH {ms:.0f}ms", file=sys.stderr, flush=True)
