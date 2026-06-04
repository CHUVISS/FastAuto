from __future__ import annotations

import asyncio
import io
import logging
import os
import uuid
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageStorage(ABC):
    @abstractmethod
    async def save(self, owner_id: uuid.UUID, filename: str, data: bytes) -> str: ...

    @abstractmethod
    async def delete(self, owner_id: uuid.UUID, filename: str) -> None: ...

    @abstractmethod
    async def read(self, owner_id: uuid.UUID, filename: str) -> bytes | None: ...

    async def copy_file(
        self,
        src_owner: uuid.UUID,
        src_filename: str,
        dst_owner: uuid.UUID,
        dst_filename: str,
    ) -> str | None:
        data = await self.read(src_owner, src_filename)
        if data is None:
            logger.warning("copy_file: src не найден %s/%s", src_owner, src_filename)
            return None
        return await self.save(dst_owner, dst_filename, data)

    @abstractmethod
    async def cleanup_tmp(self) -> None: ...


class LocalImageStorage(ImageStorage):
    def __init__(self, upload_dir: str) -> None:
        self._root = Path(upload_dir)

    def _owner_dir(self, owner_id: uuid.UUID) -> Path:
        return self._root / "cars" / str(owner_id)

    def _ensure_owner_dir(self, owner_id: uuid.UUID) -> Path:
        path = self._owner_dir(owner_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _public_url(owner_id: uuid.UUID, filename: str) -> str:
        return f"/uploads/cars/{owner_id}/{filename}"

    async def save(self, owner_id: uuid.UUID, filename: str, data: bytes) -> str:
        dest = self._ensure_owner_dir(owner_id) / filename
        tmp = dest.with_suffix(".tmp")
        try:
            await asyncio.to_thread(self._atomic_write, data, tmp, dest)
        except Exception as exc:
            logger.error("LocalStorage.save failed %s: %s", filename, exc)
            raise
        return self._public_url(owner_id, filename)

    @staticmethod
    def _atomic_write(data: bytes, tmp: Path, dest: Path) -> None:
        try:
            tmp.write_bytes(data)
            tmp.rename(dest)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    async def read(self, owner_id: uuid.UUID, filename: str) -> bytes | None:
        path = self._owner_dir(owner_id) / filename
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError:
            return None

    async def delete(self, owner_id: uuid.UUID, filename: str) -> None:
        path = self._owner_dir(owner_id) / filename
        await asyncio.to_thread(path.unlink, True)

    async def cleanup_tmp(self) -> None:
        if not self._root.exists():
            return
        removed = 0
        for tmp in self._root.rglob("*.tmp"):
            tmp.unlink(missing_ok=True)
            removed += 1
        if removed:
            logger.warning("Cleaned up %d orphaned .tmp files", removed)


class MinioImageStorage(ImageStorage):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        public_base_url: str,
    ) -> None:
        from minio import Minio

        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
            logger.info("MinIO bucket created: %s", self._bucket)

    @staticmethod
    def _object_name(owner_id: uuid.UUID, filename: str) -> str:
        return f"cars/{owner_id}/{filename}"

    def _public_url(self, owner_id: uuid.UUID, filename: str) -> str:
        return f"{self._public_base_url}/{self._bucket}/{self._object_name(owner_id, filename)}"

    def _sync_save(self, owner_id: uuid.UUID, filename: str, data: bytes) -> str:
        object_name = self._object_name(owner_id, filename)
        self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type="image/jpeg",
        )
        return self._public_url(owner_id, filename)

    def _sync_read(self, owner_id: uuid.UUID, filename: str) -> bytes | None:
        from minio.error import S3Error

        object_name = self._object_name(owner_id, filename)
        response = None
        try:
            response = self._client.get_object(self._bucket, object_name)
            return response.read()
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return None
            raise
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def _sync_delete(self, owner_id: uuid.UUID, filename: str) -> None:
        from minio.error import S3Error

        object_name = self._object_name(owner_id, filename)
        try:
            self._client.remove_object(self._bucket, object_name)
        except S3Error as exc:
            if exc.code != "NoSuchKey":
                raise

    async def save(self, owner_id: uuid.UUID, filename: str, data: bytes) -> str:
        return await asyncio.to_thread(self._sync_save, owner_id, filename, data)

    async def read(self, owner_id: uuid.UUID, filename: str) -> bytes | None:
        return await asyncio.to_thread(self._sync_read, owner_id, filename)

    async def delete(self, owner_id: uuid.UUID, filename: str) -> None:
        await asyncio.to_thread(self._sync_delete, owner_id, filename)

    async def cleanup_tmp(self) -> None:
        pass


@lru_cache(maxsize=1)
def get_image_storage() -> ImageStorage:
    if settings.STORAGE_BACKEND == "minio":
        return MinioImageStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
            public_base_url=settings.MINIO_PUBLIC_URL,
        )
    return LocalImageStorage(settings.UPLOAD_DIR)


StorageDep = Annotated[ImageStorage, Depends(get_image_storage)]


def setup_local_storage(app: FastAPI, settings: Any) -> None:
    if settings.STORAGE_BACKEND != "local":
        return
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
