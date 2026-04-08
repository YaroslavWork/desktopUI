"""MPRIS2 (Media Player Remote Interfacing) over session D-Bus — no playerctl required."""

from __future__ import annotations

from typing import Any

gi = __import__("gi")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
ROOT_IFACE = "org.mpris.MediaPlayer2"
PROPS_IFACE = "org.freedesktop.DBus.Properties"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
DBUS_NAME = "org.freedesktop.DBus"


def _bus():
    try:
        return Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except Exception:
        return None


def _list_mpris_names(bus: Gio.DBusConnection) -> list[str]:
    try:
        dbus = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            DBUS_NAME,
            "/org/freedesktop/DBus",
            DBUS_NAME,
            None,
        )
        result = dbus.call_sync(
            "ListNames",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        raw = result.unpack()
        if isinstance(raw, tuple) and len(raw) == 1 and isinstance(raw[0], list):
            names = raw[0]
        elif isinstance(raw, list):
            names = raw
        else:
            names = []
    except Exception:
        return []
    out = [n for n in names if isinstance(n, str) and n.startswith(f"{ROOT_IFACE}.")]
    return sorted(out)


def _prop_get(bus: Gio.DBusConnection, dest: str, iface: str, name: str) -> Any | None:
    try:
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            dest,
            MPRIS_PATH,
            PROPS_IFACE,
            None,
        )
        v = proxy.call_sync(
            "Get",
            GLib.Variant("(ss)", (iface, name)),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        inner = v.unpack()
        if isinstance(inner, tuple) and len(inner) == 1:
            inner = inner[0]
        return inner
    except Exception:
        return None


def _pick_best_player(bus: Gio.DBusConnection, names: list[str]) -> str | None:
    if not names:
        return None
    best: tuple[int, str] | None = None
    rank_map = {"Playing": 3, "Paused": 2, "Stopped": 1}
    for name in names:
        st = _prop_get(bus, name, PLAYER_IFACE, "PlaybackStatus")
        r = rank_map.get(st if isinstance(st, str) else "", 0)
        if best is None or r > best[0]:
            best = (r, name)
    return best[1] if best else names[0]


def _call_player(bus: Gio.DBusConnection, dest: str, method: str) -> bool:
    try:
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            dest,
            MPRIS_PATH,
            PLAYER_IFACE,
            None,
        )
        proxy.call_sync(method, None, Gio.DBusCallFlags.NONE, -1, None)
        return True
    except Exception:
        return False


def _call_raise(bus: Gio.DBusConnection, dest: str) -> bool:
    try:
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            dest,
            MPRIS_PATH,
            ROOT_IFACE,
            None,
        )
        proxy.call_sync("Raise", None, Gio.DBusCallFlags.NONE, -1, None)
        return True
    except Exception:
        return False


def _deep_unpack_value(val: Any) -> Any:
    """Flatten GLib.Variant, byte strings, and nested structures from MPRIS a{sv}."""
    while isinstance(val, GLib.Variant):
        val = val.unpack()
    if isinstance(val, dict):
        return {
            (
                k.decode("utf-8", errors="replace")
                if isinstance(k, bytes)
                else str(k)
            ): _deep_unpack_value(v)
            for k, v in val.items()
        }
    if isinstance(val, (list, tuple)):
        return [_deep_unpack_value(x) for x in val]
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except Exception:
            return val
    return val


def _normalize_metadata(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    v = raw
    while isinstance(v, GLib.Variant):
        v = v.unpack()
    if not isinstance(v, dict):
        return {}
    return _deep_unpack_value(v)


def _scalar_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)) and v:
        return _scalar_text(v[0])
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace").strip()
    s = str(v).strip() if v else ""
    return s


def _artist_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        parts = [_scalar_text(x) for x in v if x]
        return ", ".join(p for p in parts if p)
    return _scalar_text(v)


def _normalize_status(raw: Any) -> str | None:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except Exception:
            return None
    return raw if isinstance(raw, str) else None


def _parse_metadata(meta_raw: Any, playback_status: str | None) -> dict[str, Any]:
    """Extract display fields and mpris:artUrl; Spotify often needs full Variant flattening."""
    meta = _normalize_metadata(meta_raw)
    title = _scalar_text(
        meta.get("xesam:title")
        or meta.get("title")
        or meta.get("xesam:asText")
    )
    artist = _artist_text(meta.get("xesam:artist") or meta.get("artist"))
    album = _scalar_text(meta.get("xesam:album") or meta.get("album"))
    art_url = _scalar_text(
        meta.get("mpris:artUrl")
        or meta.get("mpris:arturl")
        or meta.get("artUrl")
    )

    if not title:
        title = _scalar_text(meta.get("vlc:title") or meta.get("rhythmbox:streamTitle"))

    if not title and playback_status == "Playing":
        title = "Playing…"

    tip_parts = [x for x in (title, artist, album) if x]
    tip_body = "\n".join(tip_parts) if tip_parts else "Nothing playing"

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "art_url": art_url if art_url else None,
        "tip_body": tip_body,
    }


def _player_display_name(dest: str) -> str:
    return dest.removeprefix(f"{ROOT_IFACE}.")


class MprisService:
    """Talk to the best-effort active MPRIS player on the session bus."""

    _cached_dest: str | None = None

    def list_player_names(self) -> list[str]:
        bus = _bus()
        if not bus:
            return []
        return _list_mpris_names(bus)

    def select_player(self, dest: str | None) -> bool:
        """Pin controls to a specific MPRIS bus name (must currently exist on the bus)."""
        if dest is None:
            self._cached_dest = None
            return True
        bus = _bus()
        if not bus:
            return False
        if dest in _list_mpris_names(bus):
            self._cached_dest = dest
            return True
        return False

    def get_players_overview(self) -> list[dict[str, Any]]:
        """One row per MPRIS player: separate control targets on the same session bus."""
        bus = _bus()
        if not bus:
            return []
        names = _list_mpris_names(bus)
        active = self._cached_dest
        rows: list[dict[str, Any]] = []
        for dest in names:
            st_raw = _prop_get(bus, dest, PLAYER_IFACE, "PlaybackStatus")
            st = _normalize_status(st_raw)
            label = _player_display_name(dest)
            identity = _prop_get(bus, dest, ROOT_IFACE, "Identity")
            desktop = _prop_get(bus, dest, ROOT_IFACE, "DesktopEntry")
            rows.append(
                {
                    "player": dest,
                    "label": label,
                    "label_short": label[:14] + ("…" if len(label) > 14 else ""),
                    "status": st,
                    "playing": st == "Playing",
                    "paused": st == "Paused",
                    "is_active": dest == active,
                    "identity": identity if isinstance(identity, str) else None,
                    "desktop_entry": desktop if isinstance(desktop, str) else None,
                }
            )
        return rows

    def _bus_dest(self) -> tuple[Gio.DBusConnection | None, str | None]:
        bus = _bus()
        if not bus:
            return None, None
        names = _list_mpris_names(bus)
        if not names:
            self._cached_dest = None
            return bus, None
        if self._cached_dest and self._cached_dest in names:
            return bus, self._cached_dest
        self._cached_dest = _pick_best_player(bus, names)
        return bus, self._cached_dest

    def _snapshot_for(
        self,
        bus: Gio.DBusConnection,
        dest: str,
        *,
        player_count: int | None = None,
    ) -> dict[str, Any]:
        status = _prop_get(bus, dest, PLAYER_IFACE, "PlaybackStatus")
        status_s = _normalize_status(status)
        meta = _prop_get(bus, dest, PLAYER_IFACE, "Metadata")
        parsed = _parse_metadata(meta, status_s)
        title = parsed["title"]
        artist = parsed["artist"]
        album = parsed["album"]
        tip_body = parsed["tip_body"]
        art_url = parsed["art_url"]
        vol = _prop_get(bus, dest, PLAYER_IFACE, "Volume")
        v_float: float | None = None
        if isinstance(vol, float):
            v_float = vol
        n = player_count if player_count is not None else len(_list_mpris_names(bus))
        hint = (
            "\n\n—\nScroll: change volume · Right-click: raise player\n"
            "Middle-click: cycle player · Click a source tab when several are open"
            if n > 1
            else "\n\n—\nScroll: change volume · Right-click: raise player\nMiddle-click: cycle player"
        )
        short_player = _player_display_name(dest)
        full_tip = f"{tip_body}\n\nPlayer: {short_player}{hint}"
        return {
            "player": dest,
            "status": status_s,
            "title": title,
            "artist": artist,
            "album": album,
            "art_url": art_url,
            "tooltip": full_tip,
            "volume": v_float,
            "player_count": n,
        }

    def get_snapshot(self) -> dict[str, Any]:
        """Playback info for UI: player, status, title, artist, album, volume 0..1 or None."""
        bus, dest = self._bus_dest()
        if not bus or not dest:
            return {
                "player": None,
                "status": None,
                "title": "",
                "artist": "",
                "album": "",
                "art_url": None,
                "tooltip": "No MPRIS player — open Spotify, VLC, etc.\n\nScroll: volume · Right-click: focus player",
                "volume": None,
                "player_count": 0,
            }
        names = _list_mpris_names(bus)
        return self._snapshot_for(bus, dest, player_count=len(names))

    def play_pause(self) -> None:
        bus, dest = self._bus_dest()
        if bus and dest:
            _call_player(bus, dest, "PlayPause")

    def next_track(self) -> None:
        bus, dest = self._bus_dest()
        if bus and dest:
            _call_player(bus, dest, "Next")

    def previous_track(self) -> None:
        bus, dest = self._bus_dest()
        if bus and dest:
            _call_player(bus, dest, "Previous")

    def raise_player(self) -> None:
        bus, dest = self._bus_dest()
        if bus and dest:
            _call_raise(bus, dest)

    def set_volume_delta(self, delta: float) -> float | None:
        """Add delta to volume (clamped 0..1). Returns new volume or None if unsupported."""
        bus, dest = self._bus_dest()
        if not bus or not dest:
            return None
        vol = _prop_get(bus, dest, PLAYER_IFACE, "Volume")
        if not isinstance(vol, float):
            return None
        nv = max(0.0, min(1.0, vol + delta))
        try:
            proxy = Gio.DBusProxy.new_sync(
                bus,
                Gio.DBusProxyFlags.NONE,
                None,
                dest,
                MPRIS_PATH,
                PROPS_IFACE,
                None,
            )
            proxy.call_sync(
                "Set",
                GLib.Variant("(ssv)", (PLAYER_IFACE, "Volume", GLib.Variant.new_double(nv))),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            return nv
        except Exception:
            return None

    def cycle_player(self) -> str | None:
        """Prefer the next MPRIS name lexicographically (simple cycle). Returns new dest or None."""
        bus = _bus()
        if not bus:
            return None
        names = _list_mpris_names(bus)
        if not names:
            self._cached_dest = None
            return None
        if not self._cached_dest or self._cached_dest not in names:
            self._cached_dest = names[0]
            return self._cached_dest
        i = names.index(self._cached_dest)
        self._cached_dest = names[(i + 1) % len(names)]
        return self._cached_dest


mpris_service = MprisService()
