from __future__ import annotations

import io

from PIL import Image


def jpeg_bytes(
    width: int = 800, height: int = 600, color: tuple = (255, 0, 0)
) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="JPEG")
    return buf.getvalue()


def png_bytes(width: int = 800, height: int = 600, color: tuple = (0, 255, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


def webp_bytes(
    width: int = 800, height: int = 600, color: tuple = (0, 0, 255)
) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="WEBP")
    return buf.getvalue()


def pixel_bomb_jpeg() -> bytes:
    return jpeg_bytes(width=8000, height=8000)


def truncated_jpeg() -> bytes:
    return jpeg_bytes()[:50]


def fake_jpeg_with_real_magic() -> bytes:
    return b"\xff\xd8\xff" + b"\x00" * 1024
