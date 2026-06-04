"""Shared helpers + fixtures for reservation-domain tests."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user


def make_engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


async def verify_phone(eng, user_id: str, phone: str = "79991234567") -> None:
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE users SET phone_verified = true, phone = :p WHERE id = :id"),
            {"id": user_id, "p": phone},
        )


async def seed_active_listing(eng, seller_id: str, *, with_address: bool = True) -> str:
    listing_id = str(uuid.uuid4())
    address = "Москва, ул. Пример, 1" if with_address else None
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.modifications (id) VALUES ('M1') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, status, "
                "license_plate_edit_count, sale_address, accepts_cash, viewing_enabled) "
                "VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', "
                "'good', '7700000000000', 'active', 0, :addr, true, true)"
            ),
            {"id": listing_id, "s": seller_id, "addr": address},
        )
    return listing_id


async def seed_window(eng, listing_id: str, *, day_offset: int = 1) -> str:
    window_id = str(uuid.uuid4())
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, time_from, "
                "time_to) VALUES (:id, :lid, :d, '10:00', '11:00')"
            ),
            {
                "id": window_id,
                "lid": listing_id,
                "d": date.today() + timedelta(days=day_offset),
            },
        )
    return window_id


def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest_asyncio.fixture
async def reservation_world(committed_client, pg_container):
    """Seller + verified buyer + active listing + viewing window."""
    eng = make_engine(pg_container)
    seller_id = await seed_user(eng, "user", f"seller_{uuid.uuid4().hex[:6]}@e.com")
    buyer_id = await seed_user(eng, "user", f"buyer_{uuid.uuid4().hex[:6]}@e.com")
    await verify_phone(eng, buyer_id)
    listing_id = await seed_active_listing(eng, seller_id)
    window_id = await seed_window(eng, listing_id)
    await eng.dispose()
    return {
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "listing_id": listing_id,
        "window_id": window_id,
        "buyer_headers": auth_headers(buyer_id),
        "seller_headers": auth_headers(seller_id),
    }
