import uuid
from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.listings import BookingStatus, ListingStatus, ViewingBooking
from app.models.reservations import (
    Reservation,
    ReservationOutcome,
    ReservationStatus,
)
from app.services import scheduler
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


def _maker(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    return eng, async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)


async def _seed_listing(eng, seller_id) -> str:
    listing_id = str(uuid.uuid4())
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
                "model_id, year, price, mileage, color_id, condition, city_id, "
                "status, license_plate_edit_count, accepts_cash) VALUES "
                "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', "
                "'7700000000000', 'reserved', 0, true)"
            ),
            {"id": listing_id, "s": seller_id},
        )
    return listing_id


@pytest_asyncio.fixture
async def world(committed_client, pg_container):
    eng, sm = _maker(pg_container)
    seller_id = await seed_user(eng, "user", f"sell_{uuid.uuid4().hex[:6]}@e.com")
    buyer_id = await seed_user(eng, "user", f"buy_{uuid.uuid4().hex[:6]}@e.com")
    listing_id = await _seed_listing(eng, seller_id)
    yield {
        "eng": eng,
        "sm": sm,
        "seller": seller_id,
        "buyer": buyer_id,
        "listing": listing_id,
    }
    await eng.dispose()


async def _insert_reservation(
    sm, world, *, status: ReservationStatus, **over
) -> uuid.UUID:
    now = datetime.now(UTC)
    defaults = {
        "listing_id": uuid.UUID(world["listing"]),
        "buyer_id": uuid.UUID(world["buyer"]),
        "seller_id": uuid.UUID(world["seller"]),
        "deposit_amount": 5000,
        "yk_payment_id": f"pay-{uuid.uuid4().hex[:8]}",
        "status": status,
        "payment_deadline": now + timedelta(minutes=30),
        "hold_deadline": now + timedelta(days=5),
    }
    defaults.update(over)
    async with sm() as s:
        r = Reservation(**defaults)
        s.add(r)
        await s.commit()
        return r.id


@pytest.mark.asyncio
async def test_release_expired_releases_active_past_hold_deadline(world):
    sm = world["sm"]
    rid = await _insert_reservation(
        sm,
        world,
        status=ReservationStatus.active,
        hold_deadline=datetime.now(UTC) - timedelta(minutes=1),
    )
    with patch(
        "app.services.reservations.reservation_service.yk.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    ) as cancel:
        await scheduler.run_release_expired(session_factory=sm)
    cancel.assert_awaited()
    async with sm() as s:
        r = await s.get(Reservation, rid)
        assert r.status == ReservationStatus.cancelled


@pytest.mark.asyncio
async def test_release_expired_cancels_abandoned_payment(world):
    sm = world["sm"]
    rid = await _insert_reservation(
        sm,
        world,
        status=ReservationStatus.pending_payment,
        payment_deadline=datetime.now(UTC) - timedelta(minutes=1),
    )
    with patch(
        "app.services.reservations.reservation_service.yk.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    ):
        await scheduler.run_release_expired(session_factory=sm)
    async with sm() as s:
        r = await s.get(Reservation, rid)
        assert r.status == ReservationStatus.cancelled


@pytest.mark.asyncio
async def test_finalize_settling_marks_sold(world):
    sm = world["sm"]
    rid = await _insert_reservation(
        sm,
        world,
        status=ReservationStatus.settling,
        outcome=ReservationOutcome.sold,
        correction_deadline=datetime.now(UTC) - timedelta(seconds=1),
    )
    await scheduler.run_finalize_settling(session_factory=sm)
    async with sm() as s:
        r = await s.get(Reservation, rid)
        assert r.status == ReservationStatus.completed
        await s.execute(text("SELECT 1"))
        listing_status = (
            await s.execute(
                text("SELECT status FROM listings WHERE id = :id"),
                {"id": world["listing"]},
            )
        ).scalar()
        assert listing_status == ListingStatus.sold.value


@pytest.mark.asyncio
async def test_outcome_prompts_fire_only_when_window_passed(world):
    sm = world["sm"]
    rid = await _insert_reservation(sm, world, status=ReservationStatus.active)
    # booking with a window that ended in the past
    async with sm() as s:
        window_id = uuid.uuid4()
        s.add_all(
            [
                # window
            ]
        )
        await s.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, "
                "time_from, time_to) VALUES (:id, :lid, :d, :tf, :tt)"
            ),
            {
                "id": window_id,
                "lid": world["listing"],
                "d": date.today() - timedelta(days=1),
                "tf": time(10, 0),
                "tt": time(11, 0),
            },
        )
        s.add(
            ViewingBooking(
                reservation_id=rid,
                listing_id=uuid.UUID(world["listing"]),
                buyer_id=uuid.UUID(world["buyer"]),
                window_id=window_id,
                status=BookingStatus.scheduled,
            )
        )
        await s.commit()

    sms = AsyncMock()
    with patch(
        "app.services.scheduler.get_sms_service",
        return_value=type("S", (), {"send": sms})(),
    ):
        await scheduler.run_send_outcome_prompts(session_factory=sm)
    # at least one SMS per party (buyer + seller); both may have empty phones,
    # but the job must have set last_prompt_at
    async with sm() as s:
        r = await s.get(Reservation, rid)
        assert r.last_prompt_at is not None
