from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.storage import LocalImageStorage, MinioImageStorage, get_image_storage

pytestmark = pytest.mark.unit


def _make_s3_error(code):
    from minio.error import S3Error

    response = MagicMock()
    response.status = 403 if code == "AccessDenied" else 404
    response.headers = {}
    return S3Error(
        response=response,
        code=code,
        message="mocked error",
        resource="/test",
        request_id="req-1",
        host_id="host-1",
    )


BUCKET = "test-bucket"
PUBLIC_BASE = "http://localhost:9000"


@pytest.fixture
def minio_storage():
    with patch("app.core.storage.MinioImageStorage._ensure_bucket"):
        storage = MinioImageStorage(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="s",
            bucket=BUCKET,
            secure=False,
            public_base_url=PUBLIC_BASE,
        )
    storage._client = MagicMock()
    return storage


@pytest.fixture
def owner_id():
    return uuid.uuid4()


async def test_minio_save_calls_put_object(minio_storage, owner_id):
    data = b"fake-image"
    await minio_storage.save(owner_id, "img.jpg", data)

    minio_storage._client.put_object.assert_called_once()
    call_kwargs = minio_storage._client.put_object.call_args

    args, kwargs = call_kwargs
    bucket_arg = args[0] if args else kwargs.get("bucket_name")
    object_arg = args[1] if len(args) > 1 else kwargs.get("object_name")

    assert bucket_arg == BUCKET
    assert object_arg == f"cars/{owner_id}/img.jpg"


async def test_minio_save_returns_public_url(minio_storage, owner_id):
    url = await minio_storage.save(owner_id, "photo.jpg", b"data")
    expected = f"{PUBLIC_BASE}/{BUCKET}/cars/{owner_id}/photo.jpg"
    assert url == expected


async def test_minio_read_returns_bytes(minio_storage, owner_id):
    mock_response = MagicMock()
    mock_response.read.return_value = b"image-data"
    minio_storage._client.get_object.return_value = mock_response

    result = await minio_storage.read(owner_id, "img.jpg")
    assert result == b"image-data"


async def test_minio_read_returns_none_for_no_such_key(minio_storage, owner_id):
    minio_storage._client.get_object.side_effect = _make_s3_error("NoSuchKey")

    result = await minio_storage.read(owner_id, "missing.jpg")
    assert result is None


async def test_minio_read_releases_response(minio_storage, owner_id):
    mock_response = MagicMock()
    mock_response.read.return_value = b"bytes"
    minio_storage._client.get_object.return_value = mock_response

    await minio_storage.read(owner_id, "img.jpg")

    mock_response.close.assert_called_once()
    mock_response.release_conn.assert_called_once()


async def test_minio_delete_silent_for_missing_key(minio_storage, owner_id):
    minio_storage._client.remove_object.side_effect = _make_s3_error("NoSuchKey")

    await minio_storage.delete(owner_id, "ghost.jpg")


async def test_minio_delete_raises_other_s3_errors(minio_storage, owner_id):
    from minio.error import S3Error

    minio_storage._client.remove_object.side_effect = _make_s3_error("AccessDenied")

    with pytest.raises(S3Error) as exc_info:
        await minio_storage.delete(owner_id, "restricted.jpg")

    assert exc_info.value.code == "AccessDenied"


def test_minio_ensure_bucket_creates_if_missing():
    with patch("app.core.storage.MinioImageStorage._ensure_bucket"):
        storage = MinioImageStorage(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="s",
            bucket=BUCKET,
            secure=False,
            public_base_url=PUBLIC_BASE,
        )
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = False
    storage._client = mock_client

    storage._ensure_bucket()

    mock_client.make_bucket.assert_called_once_with(BUCKET)


def test_minio_ensure_bucket_skips_if_exists():
    with patch("app.core.storage.MinioImageStorage._ensure_bucket"):
        storage = MinioImageStorage(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="s",
            bucket=BUCKET,
            secure=False,
            public_base_url=PUBLIC_BASE,
        )
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    storage._client = mock_client

    storage._ensure_bucket()

    mock_client.make_bucket.assert_not_called()


@pytest.fixture(autouse=True)
def _clear_storage_cache():
    get_image_storage.cache_clear()
    yield
    get_image_storage.cache_clear()


def test_get_image_storage_returns_local_by_default(monkeypatch):
    monkeypatch.setattr("app.core.storage.settings.STORAGE_BACKEND", "local")
    monkeypatch.setattr("app.core.storage.settings.UPLOAD_DIR", "/tmp/uploads")

    storage = get_image_storage()
    assert isinstance(storage, LocalImageStorage)


def test_get_image_storage_returns_minio_when_configured(monkeypatch):
    monkeypatch.setattr("app.core.storage.settings.STORAGE_BACKEND", "minio")
    monkeypatch.setattr("app.core.storage.settings.MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setattr("app.core.storage.settings.MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setattr("app.core.storage.settings.MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setattr("app.core.storage.settings.MINIO_BUCKET", "cars")
    monkeypatch.setattr("app.core.storage.settings.MINIO_SECURE", False)
    monkeypatch.setattr(
        "app.core.storage.settings.MINIO_PUBLIC_URL", "http://localhost:9000"
    )

    with (
        patch("app.core.storage.MinioImageStorage._ensure_bucket"),
        patch("minio.Minio.__init__", return_value=None),
    ):
        storage = get_image_storage()

    assert isinstance(storage, MinioImageStorage)
