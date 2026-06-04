from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.core.config import settings
from app.core.db import async_session_factory
from app.models.listings import Listing, ListingStatus
from app.utils.masking import mask_tail

logger = logging.getLogger(__name__)

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": (
                "Поиск объявлений о продаже автомобилей по фильтрам. "
                "Используй когда пользователь спрашивает о доступных авто, "
                "ценах, характеристиках или хочет найти что-то конкретное."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mark": {
                        "type": "string",
                        "description": "Марка автомобиля (например: Toyota, BMW, Lada)",
                    },
                    "model": {
                        "type": "string",
                        "description": "Модель автомобиля (например: Camry, X5, Vesta)",
                    },
                    "year_from": {
                        "type": "integer",
                        "description": "Год выпуска от (включительно)",
                        "minimum": 1900,
                        "maximum": 2100,
                    },
                    "year_to": {
                        "type": "integer",
                        "description": "Год выпуска до (включительно)",
                        "minimum": 1900,
                        "maximum": 2100,
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Максимальная цена в рублях",
                        "minimum": 0,
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Минимальная цена в рублях",
                        "minimum": 0,
                    },
                    "max_mileage": {
                        "type": "integer",
                        "description": "Максимальный пробег в км",
                        "minimum": 0,
                    },
                    "body_type": {
                        "type": "string",
                        "description": "Тип кузова",
                    },
                    "city": {
                        "type": "string",
                        "description": "Город продажи",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_listing_details",
            "description": (
                "Получить подробную информацию об одном объявлении по ID. "
                "Используй после search_listings если пользователь хочет узнать больше."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "string",
                        "description": "UUID объявления из результатов search_listings",
                    },
                },
                "required": ["listing_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_catalog_summary",
            "description": (
                "Получить сводную статистику: количество объявлений, "
                "диапазон цен, доступные марки. "
                "Используй когда пользователь спрашивает 'что у вас есть', "
                "'сколько машин' и т.п."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_SAFE_TOOL_LOG_KEYS: frozenset[str] = frozenset(
    {
        "mark",
        "model",
        "year_from",
        "year_to",
        "max_price",
        "min_price",
        "max_mileage",
        "body_type",
        "city",
        "listing_id",
    }
)


def _redact(args: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in args.items() if k in _SAFE_TOOL_LOG_KEYS}


def validate_search_args(args: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}

    for text_field in ("mark", "model", "body_type", "city"):
        value = args.get(text_field)
        if isinstance(value, str) and 0 < len(value) <= 100:
            clean[text_field] = value.strip()

    for int_field in ("year_from", "year_to", "max_mileage", "max_price", "min_price"):
        if (val := args.get(int_field)) is not None:
            try:
                iv = int(val)
            except (TypeError, ValueError):
                continue
            if int_field in ("year_from", "year_to") and not (1900 <= iv <= 2100):
                continue
            if int_field != "year_from" and int_field != "year_to" and iv < 0:
                continue
            clean[int_field] = iv

    return clean


def validate_listing_id(args: dict[str, Any]) -> str:
    listing_id = args.get("listing_id", "")
    if not isinstance(listing_id, str):
        raise ValueError("listing_id must be a string")
    try:
        uuid.UUID(listing_id)
    except ValueError as exc:
        raise ValueError(f"Invalid listing_id format: {listing_id!r}") from exc
    return listing_id


def _listing_summary(listing: Listing) -> dict[str, Any]:
    return {
        "id": str(listing.id),
        "mark": listing.mark_id,
        "model": listing.model_id,
        "year": listing.year,
        "price": listing.price,
        "mileage": listing.mileage,
        "color": listing.color_id,
        "body_type": listing.body_type,
        "engine_type": listing.engine_type,
        "city": listing.city_id,
    }


async def _db_search_listings(session: AsyncSession, args: dict[str, Any]) -> str:
    clean = validate_search_args(args)
    max_results = settings.AI_TOOL_MAX_RESULTS

    query = select(Listing).where(Listing.status == ListingStatus.active)

    if mark := clean.get("mark"):
        query = query.where(col(Listing.mark_id).ilike(f"%{mark}%"))
    if model := clean.get("model"):
        query = query.where(col(Listing.model_id).ilike(f"%{model}%"))
    if (year_from := clean.get("year_from")) is not None:
        query = query.where(Listing.year >= year_from)
    if (year_to := clean.get("year_to")) is not None:
        query = query.where(Listing.year <= year_to)
    if (max_price := clean.get("max_price")) is not None:
        query = query.where(Listing.price <= max_price)
    if (min_price := clean.get("min_price")) is not None:
        query = query.where(Listing.price >= min_price)
    if (max_mileage := clean.get("max_mileage")) is not None:
        query = query.where(Listing.mileage <= max_mileage)
    if body := clean.get("body_type"):
        query = query.where(col(Listing.body_type).ilike(f"%{body}%"))
    if city := clean.get("city"):
        query = query.where(col(Listing.city_id) == city)

    result = await session.execute(
        query.order_by(col(Listing.price).asc()).limit(max_results)
    )
    listings = result.scalars().all()

    if not listings:
        return json.dumps(
            {"found": 0, "listings": [], "message": "Объявления по запросу не найдены"},
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "found": len(listings),
            "listings": [_listing_summary(listing) for listing in listings],
        },
        ensure_ascii=False,
    )


async def _db_get_listing_details(session: AsyncSession, args: dict[str, Any]) -> str:
    listing_id = validate_listing_id(args)
    listing = await session.get(Listing, uuid.UUID(listing_id))

    if not listing:
        return json.dumps({"error": "Объявление не найдено"}, ensure_ascii=False)
    if listing.status != ListingStatus.active:
        return json.dumps({"error": "Объявление неактивно"}, ensure_ascii=False)

    return json.dumps(
        {
            **_listing_summary(listing),
            "vin": mask_tail(listing.vin),
            "condition": listing.condition.value,
            "description": listing.description,
            "status": listing.status.value,
        },
        ensure_ascii=False,
    )


async def _db_catalog_summary(session: AsyncSession, _args: dict[str, Any]) -> str:
    total = (
        await session.execute(
            select(func.count())
            .select_from(Listing)
            .where(Listing.status == ListingStatus.active)
        )
    ).scalar_one()

    if total == 0:
        return json.dumps(
            {"total_available": 0, "message": "Объявлений нет"}, ensure_ascii=False
        )

    price_result = (
        await session.execute(
            select(func.min(Listing.price), func.max(Listing.price)).where(
                Listing.status == ListingStatus.active
            )
        )
    ).one()

    marks_result = await session.execute(
        select(Listing.mark_id).where(Listing.status == ListingStatus.active).distinct()
    )
    marks = sorted({m for m in marks_result.scalars().all() if m})

    return json.dumps(
        {
            "total_available": total,
            "price_range": {"min": price_result[0], "max": price_result[1]},
            "available_marks": marks[: settings.AI_TOOL_MAX_RESULTS * 2],
        },
        ensure_ascii=False,
    )


_TOOL_MAP = {
    "search_listings": _db_search_listings,
    "get_listing_details": _db_get_listing_details,
    "get_catalog_summary": _db_catalog_summary,
}


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> tuple[str, str | None]:
    logger.info("AI tool call: %s args=%s", tool_name, _redact(arguments))
    timeout = settings.AI_TOOL_DB_TIMEOUT_SEC

    try:
        fn = _TOOL_MAP.get(tool_name)
        if fn is None:
            return (
                json.dumps({"error": f"Unknown tool: {tool_name}"}),
                f"Unknown tool: {tool_name}",
            )
        async with async_session_factory() as session:
            result = await asyncio.wait_for(fn(session, arguments), timeout=timeout)
        return result, None

    except TimeoutError:
        error = f"Tool {tool_name} timed out after {timeout}s"
        logger.error(error)
        return json.dumps({"error": "База данных не отвечает, попробуйте позже"}), error
    except ValueError as exc:
        logger.warning("Invalid args for %s: %s", tool_name, exc)
        return json.dumps({"error": "Некорректные параметры запроса"}), str(exc)
    except Exception as exc:
        error = f"Tool {tool_name} failed: {exc}"
        logger.error(error, exc_info=True)
        return json.dumps({"error": "Ошибка получения данных"}), str(exc)
