"""Wi-Fi state and control via NetworkManager (nmcli)."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from utils.main_thread_debug import main_thread_span


@dataclass
class WiFiLinkState:
    """Snapshot of the default wireless interface (excluding Wi-Fi P2P pseudo-devices)."""

    nmcli_ok: bool
    radio_on: bool
    device: str | None
    state: str  # connected | disconnected | unavailable | unknown
    ssid: str | None
    signal: int | None
    rx_bytes: int
    tx_bytes: int
    error: str | None = None


def _run_nmcli(args: list[str], timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["nmcli", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def nmcli_available() -> bool:
    try:
        r = _run_nmcli(["--version"], timeout=2)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def wifi_radio_enabled() -> bool:
    try:
        r = _run_nmcli(["radio", "wifi"], timeout=2)
        return r.returncode == 0 and r.stdout.strip().lower() == "enabled"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def primary_wifi_device() -> str | None:
    """First `wifi` device that is not the p2p slave interface."""
    try:
        r = _run_nmcli(["-t", "-f", "DEVICE,TYPE", "device"], timeout=3)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    for line in r.stdout.strip().splitlines():
        parts = line.split(":")
        if len(parts) < 2:
            continue
        dev, typ = parts[0], parts[1]
        if typ != "wifi":
            continue
        if dev.startswith("p2p-dev-"):
            continue
        return dev
    return None


def _device_state(device: str) -> str:
    try:
        r = _run_nmcli(["-g", "GENERAL.STATE", "device", "show", device], timeout=3)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "unknown"
    if r.returncode != 0:
        return "unknown"
    line = r.stdout.strip().splitlines()
    if not line:
        return "unknown"
    low = line[0].lower()
    if "connected" in low:
        return "connected"
    if "unavailable" in low:
        return "unavailable"
    if "disconnected" in low:
        return "disconnected"
    return "unknown"


def _active_wifi_ap() -> tuple[str | None, int | None]:
    """SSID and signal (0–100) for the currently associated access point, if any.

    Uses ``wifi list --rescan no`` so NetworkManager does not kick off a fresh scan
    (the default ``device wifi`` path can block the UI for many seconds).
    """
    try:
        r = _run_nmcli(
            ["-t", "-f", "ACTIVE,SSID,SIGNAL", "device", "wifi", "list", "--rescan", "no"],
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None, None
    if r.returncode != 0:
        return None, None
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(":")
        if len(parts) < 3:
            continue
        active, signal_raw = parts[0], parts[-1]
        ssid = ":".join(parts[1:-1])
        if active != "yes":
            continue
        try:
            sig = int(signal_raw)
        except ValueError:
            sig = None
        return (ssid or None, sig)
    return None, None


def _interface_totals(iface: str) -> tuple[int, int]:
    base = Path(f"/sys/class/net/{iface}/statistics")
    rx_p = base / "rx_bytes"
    tx_p = base / "tx_bytes"
    try:
        rx = int(rx_p.read_text(encoding="utf-8").strip())
        tx = int(tx_p.read_text(encoding="utf-8").strip())
        return max(0, rx), max(0, tx)
    except (ValueError, OSError):
        return 0, 0


def poll_link_state() -> WiFiLinkState:
    if not nmcli_available():
        return WiFiLinkState(
            nmcli_ok=False,
            radio_on=False,
            device=None,
            state="unknown",
            ssid=None,
            signal=None,
            rx_bytes=0,
            tx_bytes=0,
            error="nmcli not found",
        )
    radio = wifi_radio_enabled()
    dev = primary_wifi_device()
    if not dev:
        return WiFiLinkState(
            nmcli_ok=True,
            radio_on=radio,
            device=None,
            state="unavailable",
            ssid=None,
            signal=None,
            rx_bytes=0,
            tx_bytes=0,
            error="No Wi-Fi device" if radio else "Wi-Fi radio off",
        )
    st = _device_state(dev)
    ssid: str | None = None
    sig: int | None = None
    if st == "connected":
        ssid, sig = _active_wifi_ap()
        if not ssid:
            try:
                gr = _run_nmcli(["-g", "GENERAL.CONNECTION", "device", "show", dev], timeout=3)
                if gr.returncode == 0 and gr.stdout.strip():
                    ssid = gr.stdout.strip().splitlines()[0].strip() or None
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                pass
    rx, tx = _interface_totals(dev)
    err = None
    if not radio:
        err = "Wi-Fi disabled"
    elif st != "connected":
        err = None
    return WiFiLinkState(
        nmcli_ok=True,
        radio_on=radio,
        device=dev,
        state=st,
        ssid=ssid,
        signal=sig,
        rx_bytes=rx,
        tx_bytes=tx,
        error=err,
    )


def wifi_connect() -> tuple[bool, str]:
    """Turn radio on and ask NetworkManager to bring up the wireless device."""
    if not nmcli_available():
        return False, "nmcli not available"
    _run_nmcli(["radio", "wifi", "on"], timeout=5)
    _run_nmcli(["networking", "on"], timeout=5)
    dev = primary_wifi_device()
    if not dev:
        return False, "No Wi-Fi interface"
    r = _run_nmcli(["device", "connect", dev], timeout=65)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip() or "Connect failed"
        return False, msg
    return True, ""


def wifi_disconnect() -> tuple[bool, str]:
    """Disconnect the wireless device from the current network."""
    if not nmcli_available():
        return False, "nmcli not available"
    dev = primary_wifi_device()
    if not dev:
        return False, "No Wi-Fi interface"
    r = _run_nmcli(["device", "disconnect", dev], timeout=15)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip() or "Disconnect failed"
        return False, msg
    return True, ""


class WiFiService:
    def __init__(self) -> None:
        self._t_prev: float | None = None
        self._rx_prev: int | None = None
        self._tx_prev: int | None = None
        self._phase_prev: str | None = None

    def poll_link_state(self) -> WiFiLinkState:
        return poll_link_state()

    def poll_with_throughput(self) -> tuple[WiFiLinkState, float, float]:
        """Return link state plus receive/transmit throughput (bytes per second)."""
        with main_thread_span("wifi poll (nmcli + stats)"):
            st = poll_link_state()
            phase = f"{st.state}:{st.device or ''}"
            if self._phase_prev is not None and phase != self._phase_prev:
                self._t_prev = None
                self._rx_prev = None
                self._tx_prev = None
            self._phase_prev = phase

            now = time.monotonic()
            rx_bps = 0.0
            tx_bps = 0.0
            if st.state == "connected" and st.device:
                if self._t_prev is not None and self._rx_prev is not None and self._tx_prev is not None:
                    dt = now - self._t_prev
                    if dt > 0.05:
                        rx_bps = max(0.0, (st.rx_bytes - self._rx_prev) / dt)
                        tx_bps = max(0.0, (st.tx_bytes - self._tx_prev) / dt)
            self._t_prev = now
            self._rx_prev = st.rx_bytes
            self._tx_prev = st.tx_bytes
            return st, rx_bps, tx_bps

    def connect(self) -> tuple[bool, str]:
        return wifi_connect()

    def disconnect(self) -> tuple[bool, str]:
        return wifi_disconnect()


wifi_service = WiFiService()
