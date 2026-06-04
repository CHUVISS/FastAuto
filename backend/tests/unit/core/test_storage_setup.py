from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

pytestmark = pytest.mark.unit


def _settings(**kw):
    base = {"STORAGE_BACKEND": "local", "UPLOAD_DIR": "/tmp/test_uploads"}
    return SimpleNamespace(**{**base, **kw})


def test_setup_local_storage_creates_dir_and_mounts(tmp_path):
    from app.core.storage import setup_local_storage

    upload_dir = str(tmp_path / "uploads")
    app = FastAPI()
    setup_local_storage(app, _settings(UPLOAD_DIR=upload_dir))

    assert (tmp_path / "uploads").exists()
    route_names = [r.name for r in app.routes]
    assert "uploads" in route_names


def test_setup_local_storage_noop_for_minio():
    from app.core.storage import setup_local_storage

    app = MagicMock()
    setup_local_storage(app, _settings(STORAGE_BACKEND="minio"))

    app.mount.assert_not_called()


def test_setup_local_storage_idempotent(tmp_path):
    from app.core.storage import setup_local_storage

    upload_dir = str(tmp_path / "uploads")
    app = FastAPI()
    setup_local_storage(app, _settings(UPLOAD_DIR=upload_dir))

    with patch.object(app, "mount") as mock_mount:
        setup_local_storage(app, _settings(UPLOAD_DIR=upload_dir))

    mock_mount.assert_called_once()
