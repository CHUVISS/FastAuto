import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fakeredis.aioredis import FakeRedis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.reservations import Reservation, ReservationStatus
from app.services.reservations.reservation_service import build_handlers

pytestmark = pytest.mark.integration


def _sessionmaker(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    return eng, async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)


async def _seed(maker, *, status: ReservationStatus) -> tuple[str, str]:
    async with maker() as s:
        seller = await seed_user_in(s, "seller")
        buyer = await seed_user_in(s, "buyer")
        listing_id = str(uuid.uuid4())
        await s.execute(
            text(
                "INSERT INTO catalog.modifications (id) VALUES ('M1') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await s.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, status, "
                "license_plate_edit_count) VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, "
                "2500000, 1, 'black', 'good', '7700000000000', 'reserved', 0)"
            ),
            {"id": listing_id, "s": seller},
        )
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)
        r = Reservation(
            listing_id=uuid.UUID(listing_id),
            buyer_id=uuid.UUID(buyer),
            seller_id=uuid.UUID(seller),
            deposit_amount=5000,
            yk_payment_id=payment_id,
            status=status,
            payment_deadline=now + timedelta(minutes=30),
            hold_deadline=now + timedelta(days=5),
        )
        s.add(r)
        await s.commit()
        return str(r.id), payment_id


async def seed_user_in(session, role_label) -> str:
    from app.crud.users import create_user
    from app.models.users import UserRole
    from app.schemas.users import UserCreate

    u = await create_user(
        session,
        UserCreate(
            email=f"{role_label}_{uuid.uuid4().hex[:8]}@e.com",
            password="TestPass123!",
            full_name=role_label,
            role=UserRole.user,
        ),
    )
    await session.flush()
    return str(u.id)


@pytest.mark.asyncio
async def test_on_hold_confirmed_activates(pg_container, engine):  # noqa: ARG001
    eng, maker = _sessionmaker(pg_container)
    rid, payment_id = await _seed(maker, status=ReservationStatus.pending_payment)
    handlers = build_handlers(maker, FakeRedis())
    with patch(
        "app.services.reservations.reservation_service.yk.find_payment",
        new=AsyncMock(return_value=MagicMock(status="waiting_for_capture")),
    ):
        await handlers.on_hold_confirmed(payment_id)
    async with maker() as s:
        r = await s.get(Reservation, uuid.UUID(rid))
        assert r.status == ReservationStatus.active
    await eng.dispose()


@pytest.mark.asyncio
async def test_on_hold_released_cancels(pg_container, engine):  # noqa: ARG001
    eng, maker = _sessionmaker(pg_container)
    rid, payment_id = await _seed(maker, status=ReservationStatus.active)
    handlers = build_handlers(maker, FakeRedis())
    with patch(
        "app.services.reservations.reservation_service.yk.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    ):
        await handlers.on_hold_released(payment_id)
    async with maker() as s:
        r = await s.get(Reservation, uuid.UUID(rid))
        assert r.status == ReservationStatus.cancelled
    await eng.dispose()
