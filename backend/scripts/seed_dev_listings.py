from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session_factory
from app.core.log import configure_logging
from app.core.storage import get_image_storage
from app.crud.users import create_user, get_user_by_email
from app.models.users import UserRole
from app.schemas.users import UserCreate
from app.services.images.image_service import process_image

log = structlog.get_logger(__name__)

_PHOTO_DIR = Path(__file__).resolve().parent.parent / "data" / "seed_photos"


_SELLERS: list[dict[str, str]] = [
    {
        "email": "alexander.petrov@example.com",
        "full_name": "Александр Петров",
        "phone": "79161112233",
    },
    {
        "email": "dmitry.sokolov@example.com",
        "full_name": "Дмитрий Соколов",
        "phone": "79162223344",
    },
    {
        "email": "mikhail.ivanov@example.com",
        "full_name": "Михаил Иванов",
        "phone": "79163334455",
    },
    {
        "email": "elena.gromova@example.com",
        "full_name": "Елена Громова",
        "phone": "79164445566",
    },
    {
        "email": "andrey.morozov@example.com",
        "full_name": "Андрей Морозов",
        "phone": "79165556677",
    },
]
_DEFAULT_PASSWORD = "DemoSeller123!"

_LEGACY_DEMO_EMAIL = "demo-seller@example.com"


_LISTINGS: list[dict[str, Any]] = [
    {
        "seller_idx": 0,
        "model_id": "BMW_3ER",
        "photo": "bmw_3.jpg",
        "year": 2021,
        "price": 3_450_000,
        "mileage": 54_000,
        "condition": "excellent",
        "vin": "WBA8B7G55KNT12345",
        "license_plate": "А777АА77",
        "color_id": "black",
        "description": (
            "BMW 3 серии в идеальном состоянии. Один владелец по ПТС, "
            "всё ТО только у официального дилера, есть распечатка истории "
            "обслуживания. ДТП не было, гаражное хранение зимой, летом — "
            "крытый паркинг. Зимняя резина на литых дисках в подарок."
        ),
        "sale_address": "Москва, Ленинский проспект, 10",
        "days_ago": 1,
        "windows": 8,
    },
    {
        "seller_idx": 1,
        "model_id": "AUDI_RS6",
        "photo": "audi_rs6.jpg",
        "year": 2022,
        "price": 11_500_000,
        "mileage": 22_000,
        "condition": "excellent",
        "vin": "WAUZZZ4G5NN112233",
        "license_plate": "В001ВВ77",
        "color_id": "gray",
        "description": (
            "Audi RS6 Avant, заводская комплектация Performance, керамические "
            "тормоза, полный пакет Black Optic. Авто на гарантии Audi до конца "
            "2026 года. Зимний и летний комплекты колёс на оригинальных дисках. "
            "Покупался у официального дилера, документы в порядке."
        ),
        "sale_address": "Москва, Кутузовский проспект, 22",
        "days_ago": 3,
        "windows": 12,
    },
    {
        "seller_idx": 2,
        "model_id": "BMW_X5",
        "photo": "bmw_x5.jpg",
        "year": 2021,
        "price": 6_500_000,
        "mileage": 68_000,
        "condition": "good",
        "vin": "WBAJC5103LB55667X",
        "license_plate": "С222СС77",
        "color_id": "white",
        "description": (
            "BMW X5 xDrive40i, M-пакет, панорамная крыша, кожаный салон Vernasca. "
            "Два владельца по ПТС, обслуживание по регламенту в дилерском центре. "
            "Прохождение полной диагностики перед продажей доступно. Торг разумный "
            "при осмотре, документы готовы к сделке."
        ),
        "sale_address": "Москва, Большая Дмитровка, 7",
        "days_ago": 5,
        "windows": 5,
    },
    {
        "seller_idx": 2,
        "model_id": "AUDI_A6",
        "photo": "audi_a6.jpg",
        "year": 2021,
        "price": 3_900_000,
        "mileage": 71_000,
        "condition": "good",
        "vin": "WAUZZZF45MN334455",
        "license_plate": "Е333ЕЕ77",
        "color_id": "silver",
        "description": (
            "Audi A6 в кузове C8, премиальный пакет: матричные фары, проекция на "
            "лобовое, виртуальная панель Audi virtual cockpit plus. Полная "
            "сервисная история, обслуживание у дилера. Машина для тех, кто ценит "
            "комфорт длительных поездок и тихий салон."
        ),
        "sale_address": "Москва, Тверская улица, 4",
        "days_ago": 5,
        "windows": 5,
    },
    {
        "seller_idx": 3,
        "model_id": "BMW_X3",
        "photo": "bmw_x3.jpg",
        "year": 2022,
        "price": 4_900_000,
        "mileage": 38_000,
        "condition": "excellent",
        "vin": "WBAXZ91010LM77889",
        "license_plate": "Н444НН77",
        "color_id": "blue",
        "description": (
            "BMW X3 xDrive30i, заводская комплектация xLine. Один владелец, "
            "не битый, никаких следов окрасов кузова, ЛКП заводское. Машина "
            "в Москве с момента покупки, эксплуатация только по асфальту. "
            "На гарантии BMW до середины 2027 года, что подтверждается документами."
        ),
        "sale_address": "Москва, улица Профсоюзная, 7",
        "days_ago": 2,
        "windows": 3,
    },
    {
        "seller_idx": 3,
        "model_id": "AUDI_A4",
        "photo": "audi_a4.jpg",
        "year": 2020,
        "price": 2_800_000,
        "mileage": 89_000,
        "condition": "good",
        "vin": "WAUZZZ8K1LA556677",
        "license_plate": "Р555РР77",
        "color_id": "black",
        "description": (
            "Audi A4 в кузове B9, рестайлинг 2020 года, двигатель 2.0 TFSI, "
            "коробка S tronic. Сервисная книжка ведётся в дилерском центре. "
            "Подвеска без замечаний, расходники свежие: масло, фильтры, тормоза "
            "поменяны летом. Машина готова к долгой эксплуатации без вложений."
        ),
        "sale_address": "Москва, Варшавское шоссе, 18",
        "days_ago": 7,
        "windows": 3,
    },
    {
        "seller_idx": 3,
        "model_id": "AUDI_A3",
        "photo": "audi_a3.jpg",
        "year": 2019,
        "price": 2_150_000,
        "mileage": 97_000,
        "condition": "good",
        "vin": "WAUZZZ8V1KA778899",
        "license_plate": "Т666ТТ77",
        "color_id": "red",
        "description": (
            "Audi A3 Sportback, динамичная городская машина в отличном состоянии. "
            "Один владелец, регулярное обслуживание, замена расходников по "
            "регламенту. Шумоизоляция дополнительно усилена, установлена камера "
            "заднего вида и парктроник по кругу. Идеальна для города."
        ),
        "sale_address": "Москва, Дмитровское шоссе, 89",
        "days_ago": 7,
        "windows": 3,
    },
    {
        "seller_idx": 4,
        "model_id": "BMW_5ER",
        "photo": "bmw_5.jpg",
        "year": 2020,
        "price": 4_200_000,
        "mileage": 82_000,
        "condition": "good",
        "vin": "WBAJC5102LN12233X",
        "license_plate": "У777УУ77",
        "color_id": "silver",
        "description": (
            "BMW 5 серии в кузове G30, рестайлинг LCI. Конфигурация Luxury Line: "
            "кожаный салон Dakota, акустика Harman/Kardon, адаптивная подвеска. "
            "Машина на ходу, состояние соответствует пробегу. Все ТО пройдены, "
            "история обслуживания доступна для проверки."
        ),
        "sale_address": "Москва, Ленинградский проспект, 31",
        "days_ago": 14,
        "windows": 1,
    },
    {
        "seller_idx": 4,
        "model_id": "BMW_X6",
        "photo": "bmw_x6.jpg",
        "year": 2020,
        "price": 5_800_000,
        "mileage": 75_000,
        "condition": "good",
        "vin": "WBAFG8102LP34455X",
        "license_plate": "Ф888ФФ77",
        "color_id": "black",
        "description": (
            "BMW X6 третьего поколения, M-Sport пакет. Эффектный купе-кроссовер, "
            "21-дюймовые литые диски, панорамная крыша, премиальная акустика. "
            "Эксплуатация бережная, кузов и салон в очень хорошем состоянии. "
            "Полностью обслужен перед продажей: масло, тормоза, диагностика."
        ),
        "sale_address": "Москва, Звенигородское шоссе, 4",
        "days_ago": 14,
        "windows": 1,
    },
    {
        "seller_idx": 4,
        "model_id": "BMW_M3",
        "photo": "bmw_m3.jpg",
        "year": 2022,
        "price": 8_200_000,
        "mileage": 18_000,
        "condition": "excellent",
        "vin": "WBSJF0102LR56677X",
        "license_plate": "Х999ХХ77",
        "color_id": "white",
        "description": (
            "BMW M3 Competition в кузове G80. Конфигурация Carbon: карбоновые "
            "элементы экстерьера и салона, ковши, керамика. Заводская гарантия "
            "до 2027 года. Использовалась как второй автомобиль, минимальный "
            "пробег, состояние нового салона. Возможна сделка через автокредит."
        ),
        "sale_address": "Москва, Ленинский проспект, 99",
        "days_ago": 2,
        "windows": 12,
    },
    {
        "seller_idx": 4,
        "model_id": "AUDI_Q5",
        "photo": "audi_q5.jpg",
        "year": 2021,
        "price": 4_500_000,
        "mileage": 56_000,
        "condition": "excellent",
        "vin": "WAUZZZFY1MA778899",
        "license_plate": "Ц111ЦЦ77",
        "color_id": "gray",
        "description": (
            "Audi Q5 второго поколения с обновлённым дизайном. Полный привод "
            "quattro, MMI Navigation plus с MMI touch, светодиодная матричная "
            "оптика. Машина обслужена у официального дилера, все работы "
            "зафиксированы. Без аварий, без следов восстановительного ремонта."
        ),
        "sale_address": "Москва, Рублёвское шоссе, 16",
        "days_ago": 5,
        "windows": 5,
    },
    {
        "seller_idx": 4,
        "model_id": "AUDI_Q7",
        "photo": "audi_q7.jpg",
        "year": 2020,
        "price": 5_400_000,
        "mileage": 92_000,
        "condition": "good",
        "vin": "WAUZZZ4M1LA990011",
        "license_plate": "Ч222ЧЧ77",
        "color_id": "blue",
        "description": (
            "Audi Q7 в семиместной комплектации, идеален для семьи. Двигатель "
            "3.0 TFSI, восьмиступенчатый автомат tiptronic. Пневмоподвеска "
            "обслужена недавно, состояние подтверждено диагностикой. Кожаный "
            "салон без потёртостей, два комплекта колёс зима/лето в подарок."
        ),
        "sale_address": "Москва, Можайское шоссе, 12",
        "days_ago": 7,
        "windows": 8,
    },
]


async def _pick_modifications(session: AsyncSession) -> dict[str, dict[str, str]]:
    needed = sorted({spec["model_id"] for spec in _LISTINGS})
    rows = (
        await session.execute(
            text(
                "SELECT DISTINCT ON (mo.id) mo.id AS model_id, "
                "  mod.id AS modification_id, m.id AS mark_id, "
                "  c.body_type AS body_type, s.engine_type AS engine_type "
                "FROM catalog.modifications mod "
                "JOIN catalog.marks m ON m.id = mod.mark_id "
                "JOIN catalog.models mo ON mo.id = mod.model_id "
                "JOIN catalog.configurations c ON c.id = mod.configuration_id "
                "JOIN catalog.specifications s ON s.id = mod.id "
                "WHERE mo.id = ANY(:ids) "
                "  AND c.body_type IS NOT NULL "
                "  AND s.engine_type IS NOT NULL "
                "ORDER BY mo.id, mod.id"
            ),
            {"ids": needed},
        )
    ).all()
    return {r._mapping["model_id"]: dict(r._mapping) for r in rows}


async def _ensure_city(session: AsyncSession) -> str:
    moscow = (
        await session.execute(
            text("SELECT id FROM geo.cities WHERE id = '7700000000000'")
        )
    ).scalar()
    if moscow:
        return moscow
    return (
        await session.execute(
            text(
                "SELECT id FROM geo.cities "
                "WHERE is_popular = true ORDER BY population DESC NULLS LAST LIMIT 1"
            )
        )
    ).scalar()


async def _ensure_seller(session: AsyncSession, seller: dict[str, str]) -> uuid.UUID:
    phone_visible = random.choice([True, False])
    existing = await get_user_by_email(session, seller["email"])
    if existing:
        await session.execute(
            text(
                "UPDATE users SET phone = :p, phone_verified = true, "
                "phone_visible = :pv, full_name = :n WHERE id = :id"
            ),
            {
                "id": str(existing.id),
                "p": seller["phone"],
                "pv": phone_visible,
                "n": seller["full_name"],
            },
        )
        return existing.id
    user = await create_user(
        session,
        UserCreate(
            email=seller["email"],
            password=_DEFAULT_PASSWORD,
            full_name=seller["full_name"],
            role=UserRole.user,
        ),
    )
    await session.flush()
    await session.execute(
        text(
            "UPDATE users SET phone = :p, phone_verified = true, "
            "phone_visible = :pv WHERE id = :id"
        ),
        {"id": str(user.id), "p": seller["phone"], "pv": phone_visible},
    )
    return user.id


async def _save_photo(seller_id: uuid.UUID, photo_name: str) -> tuple[str, str]:
    path = _PHOTO_DIR / photo_name
    if not path.exists():
        raise FileNotFoundError(f"Seed photo missing: {path}")
    raw = path.read_bytes()
    original_bytes, thumb_bytes = await asyncio.to_thread(process_image, raw)
    stem = uuid.uuid4().hex
    storage = get_image_storage()
    url = await storage.save(seller_id, f"{stem}.jpg", original_bytes)
    thumb_url = await storage.save(seller_id, f"{stem}_thumb.jpg", thumb_bytes)
    return url, thumb_url


def _spread_windows(count: int) -> list[tuple[date, time, time]]:
    today = date.today()
    slots = [
        (time(10, 0), time(11, 0)),
        (time(11, 30), time(12, 30)),
        (time(14, 0), time(15, 0)),
        (time(16, 0), time(17, 0)),
        (time(18, 0), time(19, 0)),
    ]
    out: list[tuple[date, time, time]] = []
    day_offset = 1
    while len(out) < count:
        wdate = today + timedelta(days=day_offset)
        per_day = min(len(slots), count - len(out))
        for i in range(per_day):
            tf, tt = slots[i]
            out.append((wdate, tf, tt))
        day_offset += 1
    return out


async def _insert_listing(
    session: AsyncSession,
    *,
    seller_id: uuid.UUID,
    spec: dict[str, Any],
    mod: dict[str, str],
    city_id: str,
    photo_url: str,
    thumb_url: str,
) -> None:
    listing_id = uuid.uuid4()
    now = datetime.now(UTC)
    published_at = now - timedelta(days=spec["days_ago"])
    expires_at = published_at + timedelta(days=settings.LISTING_LIFETIME_DAYS)

    await session.execute(
        text(
            "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
            "model_id, body_type, engine_type, year, price, mileage, color_id, "
            "vin, license_plate, license_plate_edit_count, description, "
            "sale_address, accepts_cash, accepts_transfer, status, "
            "viewing_enabled, condition, city_id, published_at, expires_at) VALUES "
            "(:id, :seller_id, :modification_id, :mark_id, :model_id, "
            ":body_type, :engine_type, :year, :price, :mileage, :color_id, "
            ":vin, :license_plate, 0, :description, :sale_address, "
            "true, true, 'active', true, :condition, :city_id, "
            ":published_at, :expires_at)"
        ),
        {
            "id": str(listing_id),
            "seller_id": str(seller_id),
            "modification_id": mod["modification_id"],
            "mark_id": mod["mark_id"],
            "model_id": mod["model_id"],
            "body_type": mod["body_type"],
            "engine_type": mod["engine_type"],
            "year": spec["year"],
            "price": spec["price"],
            "mileage": spec["mileage"],
            "color_id": spec["color_id"],
            "vin": spec["vin"],
            "license_plate": spec["license_plate"],
            "description": spec["description"],
            "sale_address": spec["sale_address"],
            "condition": spec["condition"],
            "city_id": city_id,
            "published_at": published_at,
            "expires_at": expires_at,
        },
    )

    await session.execute(
        text(
            "INSERT INTO listing_images (id, listing_id, url, thumbnail_url, "
            "is_primary, sort_order) VALUES (:id, :lid, :u, :t, true, 0)"
        ),
        {
            "id": str(uuid.uuid4()),
            "lid": str(listing_id),
            "u": photo_url,
            "t": thumb_url,
        },
    )

    for wdate, tf, tt in _spread_windows(spec["windows"]):
        await session.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, "
                "time_from, time_to) VALUES (:id, :lid, :d, :tf, :tt)"
            ),
            {
                "id": str(uuid.uuid4()),
                "lid": str(listing_id),
                "d": wdate,
                "tf": tf,
                "tt": tt,
            },
        )


async def _wipe_existing(session: AsyncSession, seller_ids: list[uuid.UUID]) -> None:
    ids = [str(sid) for sid in seller_ids]
    await session.execute(
        text(
            "DELETE FROM viewing_bookings WHERE listing_id IN "
            "(SELECT id FROM listings WHERE seller_id = ANY(:ids))"
        ),
        {"ids": ids},
    )
    await session.execute(
        text(
            "DELETE FROM reservations WHERE listing_id IN "
            "(SELECT id FROM listings WHERE seller_id = ANY(:ids))"
        ),
        {"ids": ids},
    )
    await session.execute(
        text(
            "DELETE FROM listing_images WHERE listing_id IN "
            "(SELECT id FROM listings WHERE seller_id = ANY(:ids))"
        ),
        {"ids": ids},
    )
    await session.execute(
        text(
            "DELETE FROM viewing_windows WHERE listing_id IN "
            "(SELECT id FROM listings WHERE seller_id = ANY(:ids))"
        ),
        {"ids": ids},
    )
    await session.execute(
        text("DELETE FROM listings WHERE seller_id = ANY(:ids)"),
        {"ids": ids},
    )


async def main() -> None:
    if settings.ENVIRONMENT != "local":
        log.info("dev_seed_skip_non_local", environment=settings.ENVIRONMENT)
        return

    reset = os.environ.get("DEV_SEED_RESET", "").lower() in ("1", "true", "yes")

    async with async_session_factory() as session:
        city_id = await _ensure_city(session)
        if city_id is None:
            log.warning("dev_seed_skip_geo_empty")
            return

        mods = await _pick_modifications(session)
        missing = [
            spec["model_id"] for spec in _LISTINGS if spec["model_id"] not in mods
        ]
        if missing:
            log.warning("dev_seed_missing_catalog_models", models=missing)
            return

        seller_ids: list[uuid.UUID] = []
        for seller in _SELLERS:
            seller_ids.append(await _ensure_seller(session, seller))
        legacy_demo = await get_user_by_email(session, _LEGACY_DEMO_EMAIL)
        wipe_ids = list(seller_ids)
        if legacy_demo is not None:
            wipe_ids.append(legacy_demo.id)
        await session.flush()

        existing_count = (
            await session.execute(
                text("SELECT count(*) FROM listings WHERE seller_id = ANY(:ids)"),
                {"ids": [str(sid) for sid in wipe_ids]},
            )
        ).scalar_one()

        if existing_count and not reset:
            log.info(
                "dev_seed_skip_already_present",
                existing=int(existing_count),
                sellers=len(seller_ids),
            )
            await session.commit()
            return

        if existing_count and reset:
            log.info("dev_seed_reset_requested", wiping=int(existing_count))
            await _wipe_existing(session, wipe_ids)

        for spec in _LISTINGS:
            seller_id = seller_ids[spec["seller_idx"]]
            photo_url, thumb_url = await _save_photo(seller_id, spec["photo"])
            await _insert_listing(
                session,
                seller_id=seller_id,
                spec=spec,
                mod=mods[spec["model_id"]],
                city_id=city_id,
                photo_url=photo_url,
                thumb_url=thumb_url,
            )

        await session.commit()
        log.info(
            "dev_seed_done",
            sellers=len(seller_ids),
            listings=len(_LISTINGS),
        )


if __name__ == "__main__":
    configure_logging(settings)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    asyncio.run(main())
