from __future__ import annotations

import asyncio
import io
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps

from app.core.config import settings
from app.core.storage import ImageStorage

logger = logging.getLogger(__name__)

_MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"RIFF": "webp",
}


@dataclass(frozen=True)
class SavedImage:
    filename: str
    url: str
    thumb_filename: str
    thumb_url: str


def detect_image_type(raw: bytes) -> str | None:
    for magic, fmt in _MAGIC_BYTES.items():
        if raw[: len(magic)] == magic:
            if fmt == "webp" and raw[8:12] != b"WEBP":
                continue
            return fmt
    return None


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode == "P":
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img if img.mode == "RGB" else img.convert("RGB")


def process_image(raw: bytes) -> tuple[bytes, bytes]:
    img: Image.Image = Image.open(io.BytesIO(raw))

    max_px = settings.image_max_pixels
    if img.width * img.height > max_px:
        raise ValueError(
            f"Изображение слишком большое: {img.width}x{img.height} пкс. "
            f"Максимум: {settings.IMAGE_MAX_PIXELS_MP} МП"
        )

    img = ImageOps.exif_transpose(img)
    img = _to_rgb(img)

    max_dim = settings.IMAGE_MAX_DIMENSION
    if img.width > max_dim or img.height > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    original_buf = io.BytesIO()
    img.save(
        original_buf, format="JPEG", quality=settings.IMAGE_JPEG_QUALITY, optimize=True
    )

    thumb = img.copy()
    thumb_dim = settings.IMAGE_THUMB_DIMENSION
    thumb.thumbnail((thumb_dim, thumb_dim), Image.Resampling.LANCZOS)
    thumb_buf = io.BytesIO()
    thumb.save(
        thumb_buf, format="JPEG", quality=settings.IMAGE_THUMB_QUALITY, optimize=True
    )

    return original_buf.getvalue(), thumb_buf.getvalue()


def validate_upload(file: UploadFile, raw: bytes) -> None:
    if detect_image_type(raw) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Содержимое файла не соответствует поддерживаемому формату",
        )
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"Файл слишком большой: {size_mb:.1f} МБ. "
                f"Максимум: {settings.MAX_IMAGE_SIZE_MB} МБ"
            ),
        )
    if file.content_type not in settings.allowed_image_types_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Неподдерживаемый тип файла: {file.content_type}. "
                f"Разрешены: {', '.join(settings.allowed_image_types_list)}"
            ),
        )


async def validate_and_save(
    file: UploadFile,
    owner_id: uuid.UUID,
    storage: ImageStorage,
) -> SavedImage:
    raw = await file.read()
    validate_upload(file, raw)

    logger.info("Обработка изображения owner=%s файл=%s", owner_id, file.filename)

    try:
        original_bytes, thumb_bytes = await asyncio.to_thread(process_image, raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.error("Ошибка обработки owner=%s: %s", owner_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Не удалось обработать файл изображения",
        ) from exc

    stem = uuid.uuid4().hex
    filename = f"{stem}.jpg"
    thumb_filename = f"{stem}_thumb.jpg"

    url = await storage.save(owner_id, filename, original_bytes)
    try:
        thumb_url = await storage.save(owner_id, thumb_filename, thumb_bytes)
    except Exception:
        await storage.delete(owner_id, filename)
        raise

    logger.info("Изображение сохранено: %s + %s", filename, thumb_filename)
    return SavedImage(
        filename=filename,
        url=url,
        thumb_filename=thumb_filename,
        thumb_url=thumb_url,
    )


async def delete_image_files(
    owner_id: uuid.UUID,
    filename: str,
    storage: ImageStorage,
) -> None:
    stem = Path(filename).stem.removesuffix("_thumb")
    for f in (f"{stem}.jpg", f"{stem}_thumb.jpg"):
        await storage.delete(owner_id, f)
