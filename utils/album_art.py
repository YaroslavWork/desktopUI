"""Load MPRIS album art (`mpris:artUrl`) into a GdkPixbuf; uses stdlib HTTP only."""

from __future__ import annotations

import ssl
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

gi = __import__("gi")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf


def load_album_art_pixbuf(url: str | None, width: int, height: int) -> GdkPixbuf.Pixbuf | None:
    if not url or not str(url).strip():
        return None
    url = str(url).strip()
    tw, th = max(1, width), max(1, height)
    try:
        if url.startswith("file:"):
            path = unquote(urlparse(url).path)
            return GdkPixbuf.Pixbuf.new_from_file_at_size(path, tw, th)
        ctx = ssl.create_default_context()
        req = Request(url, headers={"User-Agent": "desktopUI/1.0"})
        with urlopen(req, timeout=10, context=ctx) as resp:
            data = resp.read()
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pb = loader.get_pixbuf()
        if pb is None:
            return None
        if pb.get_width() != tw or pb.get_height() != th:
            pb = pb.scale_simple(tw, th, GdkPixbuf.InterpType.BILINEAR)
        return pb
    except Exception:
        return None
