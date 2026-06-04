from __future__ import annotations

import uuid
from datetime import date, time, timedelta
from typing import Any

from httpx import AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user


def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def get_authed(client: AsyncClient, token: dict[str, str], url: str) -> Response:
    return await client.get(url, headers=token)


async def post_authed(
    client: AsyncClient, token: dict[str, str], url: str, json: Any = None
) -> Response:
    return await client.post(url, json=json, headers=token)


def engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


async def seed_role(pg_container, role: str = "user") -> tuple[str, dict[str, str]]:
    eng = engine(pg_container)
    user_id = await seed_user(eng, role, f"{role}_{uuid.uuid4().hex[:6]}@e.com")
    await eng.dispose()
    return user_id, auth_headers(user_id)


async def verify_phone(pg_container, user_id: str, phone: str | None = None) -> None:
    phone = phone or f"7999{uuid.uuid4().int % 10_000_000:07d}"
    eng = engine(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE users SET phone_verified = true, phone = :p WHERE id = :id"),
            {"id": user_id, "p": phone},
        )
    await eng.dispose()


async def seed_active_listing(
    pg_container, seller_id: str, *, with_address: bool = True
) -> str:
    eng = engine(pg_container)
    listing_id = str(uuid.uuid4())
    address = "Москва, ул. Пример, 1" if with_address else None
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.marks (id, name) VALUES ('BMW', 'BMW') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO catalog.models (id, mark_id, name) "
                "VALUES ('BMW_5', 'BMW', '5') ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO catalog.modifications (id, mark_id, model_id) "
                "VALUES ('M1', 'BMW', 'BMW_5') ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, "
                "status, license_plate_edit_count, accepts_cash, sale_address, "
                "viewing_enabled) "
                "VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', "
                "'good', '7700000000000', 'active', 0, true, :addr, false)"
            ),
            {"id": listing_id, "s": seller_id, "addr": address},
        )
    await eng.dispose()
    return listing_id


async def seed_window(pg_container, listing_id: str, *, day_offset: int = 1) -> str:
    eng = engine(pg_container)
    window_id = str(uuid.uuid4())
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, "
                "time_from, time_to) VALUES (:id, :lid, :d, '10:00', '11:00')"
            ),
            {
                "id": window_id,
                "lid": listing_id,
                "d": date.today() + timedelta(days=day_offset),
            },
        )
    await eng.dispose()
    return window_id


async def activate_reservation(pg_container, reservation_id: str) -> None:
    """Simulate the payment.waiting_for_capture webhook flipping the hold to active."""
    eng = engine(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE reservations SET status = 'active' WHERE id = :id"),
            {"id": reservation_id},
        )
    await eng.dispose()


def hold_patch():
    from unittest.mock import AsyncMock, patch

    from app.services.payments.yookassa_service import CreatedPayment

    return patch(
        "app.services.payments.yookassa_service.create_hold",
        new=AsyncMock(
            return_value=CreatedPayment(
                id=f"pay-{uuid.uuid4().hex[:6]}", confirmation_url="https://pay"
            )
        ),
    )


def cancel_patch():
    from unittest.mock import AsyncMock, patch

    return patch(
        "app.services.payments.yookassa_service.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    )


# ``time`` is re-exported for tests that build windows directly.
_ = time
