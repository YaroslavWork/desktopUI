"""Event-driven service to communicate with displays via Hyprland IPC sockets."""

from __future__ import annotations

import os
import sys
import json
import socket
import threading
import subprocess
from typing import Any
from pathlib import Path
from gi.repository import GLib

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from base import SingletonService


class DisplaysService(SingletonService):
    """Event-driven display manager communicating directly with Hyprland IPC sockets.

    Listens to real-time events like monitoradded and monitorremoved on
    socket2.sock and exposes display query/configuration methods.
    """

    __gsignals__ = {
        "monitors-changed": (GLib.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, "_socket_thread_started"):
            return
        self._socket_thread_started = True
        self._keep_running = True

        # Start a daemon thread to listen to the Hyprland event socket
        self._thread = threading.Thread(target=self._socket_reader_loop, daemon=True)
        self._thread.start()

    def _socket_reader_loop(self) -> None:
        signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not signature:
            # Hyprland is not running or env is not populated
            return

        socket_path = f"/tmp/hypr/{signature}/.socket2.sock"

        while self._keep_running:
            try:
                if not os.path.exists(socket_path):
                    threading.Event().wait(1.0)
                    continue

                client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client.connect(socket_path)
                client.settimeout(2.0)

                buffer = ""
                while self._keep_running:
                    try:
                        data = client.recv(4096)
                        if not data:
                            break
                        buffer += data.decode("utf-8", errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line:
                                continue

                            # Detect monitor additions and removals
                            if line.startswith("monitoradded>>") or line.startswith("monitorremoved>>"):
                                GLib.idle_add(self._notify_monitors_changed)
                    except socket.timeout:
                        continue
                    except Exception:
                        break
                client.close()
            except Exception:
                threading.Event().wait(2.0)

    def _notify_monitors_changed(self) -> bool:
        self.emit("monitors-changed")
        return False  # Return False to run once (standard GLib behavior)

    def list_monitors(self) -> list[dict[str, Any]]:
        """Return active monitors from `hyprctl monitors -j`."""
        try:
            r = subprocess.run(
                ["hyprctl", "monitors", "-j"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                return [m for m in data if isinstance(m, dict)]
        except Exception:
            pass
        return []

    def list_monitors_all(self) -> list[dict[str, Any]]:
        """Return all outputs from `hyprctl monitors all -j` (includes disabled)."""
        try:
            r = subprocess.run(
                ["hyprctl", "monitors", "all", "-j"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                return [m for m in data if isinstance(m, dict)]
        except Exception:
            pass
        return []

    def get_primary_monitor(self) -> dict[str, Any] | None:
        """Find and return the focused monitor dictionary, falling back to the first active."""
        monitors = self.list_monitors()
        if not monitors:
            return None
        for m in monitors:
            if m.get("focused", False):
                return m
        return monitors[0]

    def primary_output_name(self) -> str | None:
        """Return the name of the primary output."""
        primary = self.get_primary_monitor()
        return primary.get("name") if primary else None

    def set_monitor_rule(self, name: str, rule: str) -> bool:
        """Apply a raw monitor configuration rule via hyprctl."""
        try:
            r = subprocess.run(
                ["hyprctl", "keyword", "monitor", f"{name},{rule}"],
                capture_output=True,
                timeout=3,
            )
            return r.returncode == 0
        except Exception:
            return False

    def toggle_monitor(self, name: str, enable: bool) -> bool:
        """Enable or disable a monitor output by name."""
        if enable:
            all_mons = self.list_monitors_all()
            spec = "preferred,auto,1"
            for m in all_mons:
                if m.get("name") == name:
                    w = m.get("width", 1920)
                    h = m.get("height", 1080)
                    rr = m.get("refreshRate", 60)
                    x = m.get("x", 0)
                    y = m.get("y", 0)
                    scale = m.get("scale", 1.0)
                    spec = f"{w}x{h}@{rr},{x}x{y},{scale}"
                    break
            return self.set_monitor_rule(name, spec)
        else:
            return self.set_monitor_rule(name, "disable")


displays_service = DisplaysService()
