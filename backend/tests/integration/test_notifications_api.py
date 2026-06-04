"""Notification centre — list / mark-read / mark-all + a reservation wire-point."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.services.notifications import notification_service as notifications
from tests.fixtures.committed import seed_user
from tests.short_tests._helpers import (
    activate_reservation,
    cancel_patch,
    hold_patch,
    seed_active_listing,
    seed_role,
    verify_phone,
)

pytestmark = pytest.mark.integration


def _maker(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    return eng, async_sessionmaker(eng, expire_on_commit=False)


@pytest.mark.asyncio
async def test_list_mark_read_and_mark_all(committed_client: AsyncClient, pg_container):
    eng = create_async_engine(
        pg_container.get_connection_url().replace("psycopg2", "asyncpg"),
        connect_args={"statement_cache_size": 0},
    )
    user_id = await seed_user(eng, "user", f"u_{uuid.uuid4().hex[:6]}@e.com")
    await eng.dispose()
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}

    eng2, sm = _maker(pg_container)
    async with sm() as s:
        await notifications.push(
            s, user_id=uuid.UUID(user_id), notif_type="demo", payload={"k": "v"}
        )
    async with sm() as s:
        await notifications.push(s, user_id=uuid.UUID(user_id), notif_type="demo2")
    await eng2.dispose()

    listed = await committed_client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 2

    nid = rows[0]["id"]
    read = await committed_client.post(
        f"/api/v1/notifications/{nid}/read", headers=headers
    )
    assert read.status_code == 200

    unread = await committed_client.get(
        "/api/v1/notifications?unread=true", headers=headers
    )
    assert len(unread.json()) == 1

    all_read = await committed_client.post(
        "/api/v1/notifications/read-all", headers=headers
    )
    assert all_read.status_code == 200
    assert (
        len(
            (
                await committed_client.get(
                    "/api/v1/notifications?unread=true", headers=headers
                )
            ).json()
        )
        == 0
    )


@pytest.mark.asyncio
async def test_outcome_pushes_notification_to_other_party(
    committed_client: AsyncClient, pg_container, monkeypatch
):
    seller_id, seller_h = await seed_role(pg_container, role="user")
    buyer_id, buyer_h = await seed_role(pg_container, role="user")
    await verify_phone(pg_container, buyer_id)
    listing_id = await seed_active_listing(pg_container, seller_id)

    with hold_patch():
        rid = (
            await committed_client.post(
                "/api/v1/reservations", json={"listing_id": listing_id}, headers=buyer_h
            )
        ).json()["reservation_id"]
    await activate_reservation(pg_container, rid)

    # spy on push (it writes via its own session factory — prod DB, not the
    # test container — so we assert the wiring, not the row).
    spy = AsyncMock()
    monkeypatch.setattr(notifications, "push", spy)

    with cancel_patch():
        await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=buyer_h,
        )

    spy.assert_awaited_once()
    kwargs = spy.await_args.kwargs
    assert kwargs["user_id"] == uuid.UUID(seller_id)
    assert kwargs["notif_type"] == "reservation_outcome_marked"
