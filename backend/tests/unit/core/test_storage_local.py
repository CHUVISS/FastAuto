from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.storage import LocalImageStorage

pytestmark = pytest.mark.unit


@pytest.fixture
def owner_id():
    return uuid.uuid4()


@pytest.fixture
def storage(tmp_path):
    return LocalImageStorage(str(tmp_path))


async def test_local_save_creates_file(storage, owner_id, tmp_path):
    data = b"fake-image-bytes"
    await storage.save(owner_id, "img.jpg", data)

    expected = tmp_path / "cars" / str(owner_id) / "img.jpg"
    assert expected.exists()
    assert expected.read_bytes() == data


async def test_local_save_returns_public_url(storage, owner_id):
    url = await storage.save(owner_id, "photo.jpg", b"data")
    assert url == f"/uploads/cars/{owner_id}/photo.jpg"


async def test_local_save_atomic_via_tmp_rename(storage, owner_id, tmp_path):
    def failing_rename(_self, _target):
        raise OSError("simulated rename failure")

    with patch.object(Path, "rename", failing_rename):
        with pytest.raises(OSError, match="simulated rename failure"):
            await storage.save(owner_id, "img.jpg", b"bytes")

    tmp_files = list(tmp_path.rglob("*.tmp"))
    assert tmp_files == [], f"Orphaned .tmp files found: {tmp_files}"


async def test_local_read_returns_bytes(storage, owner_id):
    data = b"hello world"
    await storage.save(owner_id, "file.jpg", data)
    result = await storage.read(owner_id, "file.jpg")
    assert result == data


async def test_local_read_returns_none_for_missing(storage, owner_id):
    result = await storage.read(owner_id, "nonexistent.jpg")
    assert result is None


async def test_local_delete_removes_file(storage, owner_id, tmp_path):
    await storage.save(owner_id, "todelete.jpg", b"content")
    expected = tmp_path / "cars" / str(owner_id) / "todelete.jpg"
    assert expected.exists()

    await storage.delete(owner_id, "todelete.jpg")
    assert not expected.exists()


async def test_local_delete_silent_for_missing(storage, owner_id):
    await storage.delete(owner_id, "ghost.jpg")


async def test_local_cleanup_tmp_removes_orphans(storage, tmp_path):
    (tmp_path / "cars").mkdir(parents=True, exist_ok=True)
    orphan1 = tmp_path / "cars" / "upload1.tmp"
    orphan2 = tmp_path / "cars" / "upload2.tmp"
    orphan1.write_bytes(b"partial1")
    orphan2.write_bytes(b"partial2")

    await storage.cleanup_tmp()

    assert not orphan1.exists()
    assert not orphan2.exists()


async def test_local_copy_file_returns_none_when_src_missing(storage, owner_id):
    dst_owner = uuid.uuid4()
    result = await storage.copy_file(owner_id, "missing.jpg", dst_owner, "dst.jpg")
    assert result is None


async def test_local_copy_file_copies_data(storage, owner_id, tmp_path):
    data = b"image-data-content"
    await storage.save(owner_id, "src.jpg", data)

    dst_owner = uuid.uuid4()
    url = await storage.copy_file(owner_id, "src.jpg", dst_owner, "dst.jpg")

    assert url is not None
    dst_bytes = await storage.read(dst_owner, "dst.jpg")
    assert dst_bytes == data


async def test_local_owner_dir_not_created_in_read(storage, tmp_path):
    unknown_owner = uuid.uuid4()
    result = await storage.read(unknown_owner, "anything.jpg")

    assert result is None
    owner_dir = tmp_path / "cars" / str(unknown_owner)
    assert not owner_dir.exists()
