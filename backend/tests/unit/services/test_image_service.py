from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.services.images.image_service import (
    detect_image_type,
    process_image,
    validate_and_save,
    validate_upload,
)
from tests.helpers.images import jpeg_bytes, png_bytes, webp_bytes

pytestmark = pytest.mark.unit


def test_detect_jpeg():
    raw = b"\xff\xd8\xff" + b"\x00" * 10
    assert detect_image_type(raw) == "jpeg"


def test_detect_png():
    raw = b"\x89PNG" + b"\x00" * 10
    assert detect_image_type(raw) == "png"


def test_detect_webp():
    raw = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 10
    assert detect_image_type(raw) == "webp"


def test_detect_unknown_returns_none():
    assert detect_image_type(b"\x00\x01\x02\x03") is None


def test_detect_riff_without_webp_marker_returns_none():
    raw = b"RIFF\x00\x00\x00\x00XXXX" + b"\x00" * 10
    assert detect_image_type(raw) is None


def test_process_image_returns_jpeg_bytes():
    original, thumb = process_image(jpeg_bytes())
    assert original[:3] == b"\xff\xd8\xff"
    assert thumb[:3] == b"\xff\xd8\xff"


def test_process_image_produces_thumb_smaller_than_original():
    original, thumb = process_image(jpeg_bytes())
    assert len(thumb) <= len(original)


def test_process_image_accepts_png():
    original, thumb = process_image(png_bytes())
    assert original[:3] == b"\xff\xd8\xff"


def test_process_image_accepts_webp():
    original, thumb = process_image(webp_bytes())
    assert original[:3] == b"\xff\xd8\xff"


def test_process_image_rejects_oversized(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "IMAGE_MAX_PIXELS_MP", 0.0001)
    with pytest.raises(ValueError, match="слишком большое"):
        process_image(jpeg_bytes())


def _mock_file(content_type="image/jpeg", raw=b""):
    f = MagicMock(spec=UploadFile)
    f.content_type = content_type
    f.filename = "test.jpg"
    f.read = AsyncMock(return_value=raw)
    return f


def test_validate_upload_ok():
    f = _mock_file("image/jpeg")
    validate_upload(f, jpeg_bytes())


def test_validate_upload_unknown_content_raises_422():
    f = _mock_file("application/octet-stream")
    with pytest.raises(HTTPException) as exc:
        validate_upload(f, jpeg_bytes())
    assert exc.value.status_code == 422


def test_validate_upload_wrong_magic_raises_422():
    f = _mock_file("image/jpeg")
    with pytest.raises(HTTPException) as exc:
        validate_upload(f, b"\x00\x00\x00\x00garbage")
    assert exc.value.status_code == 422


def test_validate_upload_too_large_raises_413(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "MAX_IMAGE_SIZE_MB", 0.0)
    f = _mock_file("image/jpeg")
    with pytest.raises(HTTPException) as exc:
        validate_upload(f, jpeg_bytes())
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_and_save_stores_two_files():
    from tests.fixtures.storage import InMemoryStorage

    storage = InMemoryStorage()
    owner = uuid.uuid4()
    raw = jpeg_bytes()

    file = _mock_file("image/jpeg", raw)

    result = await validate_and_save(file, owner, storage)

    assert result.filename.endswith(".jpg")
    assert result.thumb_filename.endswith(".jpg")
    assert result.url and result.thumb_url
    assert len(storage.files) == 2
