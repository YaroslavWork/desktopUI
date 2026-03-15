import os
import subprocess
import time
from datetime import datetime
from fabric.core.service import Service, Property


class UserService(Service):
    """Service providing Linux username and current session duration."""

    @Property(str, flags="readable")
    def username(self) -> str:
        return self._username

    @Property(int, flags="readable")
    def session_seconds(self) -> int:
        return self._session_seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._username = os.getenv("USER", "unknown")
        self._session_seconds = 0
        self._session_start: float | None = None
        self._update_session_start()

    def _update_session_start(self) -> None:
        """Resolve session start timestamp from loginctl or fallback to boot time."""
        session_id = os.getenv("XDG_SESSION_ID")
        if session_id:
            try:
                result = subprocess.run(
                    ["loginctl", "show-session", session_id, "-p", "Timestamp"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if line.startswith("Timestamp="):
                            value = line.split("=", 1)[1].strip()
                            try:
                                # Microseconds since epoch
                                self._session_start = int(value) / 1_000_000
                                return
                            except ValueError:
                                pass
                            try:
                                # Human-readable (e.g. "Sun 2026-03-15 23:59:11 CET")
                                parts = value.split()
                                dt = datetime.strptime(
                                    f"{parts[1]} {parts[2]}", "%Y-%m-%d %H:%M:%S"
                                )
                                self._session_start = dt.timestamp()
                                return
                            except (ValueError, IndexError):
                                pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Fallback: use system boot time from /proc/uptime
        try:
            with open("/proc/uptime") as f:
                uptime_seconds = float(f.read().split()[0])
            self._session_start = time.time() - uptime_seconds
        except OSError:
            self._session_start = time.time()

    def refresh_session_seconds(self) -> int:
        """Update and return current session duration in seconds."""
        if self._session_start is not None:
            self._session_seconds = int(time.time() - self._session_start)
            self.notify("session-seconds")
        return self._session_seconds


user_service = UserService()
