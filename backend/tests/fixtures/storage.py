from __future__ import annotations

import uuid

from app.core.storage import ImageStorage


class InMemoryStorage(ImageStorage):
    def __init__(self):
        self.files: dict[tuple[str, str], bytes] = {}

    async def save(self, owner_id: uuid.UUID, filename: str, data: bytes) -> str:
        self.files[(str(owner_id), filename)] = data
        return f"/test/{owner_id}/{filename}"

    async def read(self, owner_id: uuid.UUID, filename: str) -> bytes | None:
        return self.files.get((str(owner_id), filename))

    async def delete(self, owner_id: uuid.UUID, filename: str) -> None:
        self.files.pop((str(owner_id), filename), None)

    async def cleanup_tmp(self) -> None:
        pass

    async def copy_file(
        self,
        src_owner: uuid.UUID,
        src_filename: str,
        dst_owner: uuid.UUID,
        dst_filename: str,
    ) -> str | None:
        data = self.files.get((str(src_owner), src_filename))
        if data is None:
            return None
        self.files[(str(dst_owner), dst_filename)] = data
        return f"/test/{dst_owner}/{dst_filename}"
