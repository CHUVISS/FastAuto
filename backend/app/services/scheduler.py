from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import Redis
from sqlmodel import col, select

if TYPE_CHECKING:
    from fastapi import FastAPI

from app.core.config import settings
from app.core.db import async_session_factory
from app.crud import listings as listing_crud
from app.crud import reservations as res_crud
from app.crud import viewings as viewings_crud
from app.models.listings import Listing, ListingStatus, ViewingWindow
from app.models.reservations import CancelReason, ReservationStatus
from app.models.users import User
from app.services.payments.errors import (
    DepositReleaseTerminalError,
    DepositReleaseTransientError,
)
from app.services.reservations import reservation_service as res_svc
from app.services.sms.sms_service import SmsSendError, get_sms_service

log = structlog.get_logger(__name__)


async def _safe_sms(sms: Any, phone: str | None, text_msg: str) -> None:
    if not phone:
        return
    try:
        await sms.send(phone, text_msg)
    except SmsSendError:
        log.warning("scheduler.sms_failed")


async def run_release_expired(*, session_factory: Any = async_session_factory) -> None:
    deps = res_svc.default_deps()
    released = 0
    async with session_factory() as session:
        reservations = await res_crud.list_expired_holds(session, datetime.now(UTC))
        for reservation in reservations:
            listing = await listing_crud.get(session, reservation.listing_id)
            if listing is None:
                continue
            booking = await viewings_crud.get_active_booking_for_reservation(
                session, reservation.id
            )
            if booking is not None:
                await viewings_crud.cancel_booking(booking)
            reason = (
                CancelReason.payment_abandoned
                if reservation.status == ReservationStatus.pending_payment
                else CancelReason.hold_expired
            )
            try:
                await res_svc.cancel(reservation, listing, reason=reason, deps=deps)
                released += 1
            except res_svc.ReservationStateError:
                log.exception(
                    "release_expired_state_error",
                    reservation_id=str(reservation.id),
                    job="release_expired",
                )
        await session.commit()
    if released:
        log.info("release_expired_done", job="release_expired", released=released)


async def run_finalize_settling(
    *, session_factory: Any = async_session_factory
) -> None:
    finalized = 0
    async with session_factory() as session:
        reservations = await res_crud.list_settling_due(session, datetime.now(UTC))
        for reservation in reservations:
            listing = await listing_crud.get(session, reservation.listing_id)
            if listing is None:
                continue
            try:
                res_svc.finalize(reservation, listing)
                finalized += 1
            except res_svc.ReservationStateError:
                log.exception(
                    "finalize_settling_failed",
                    reservation_id=str(reservation.id),
                    job="finalize_settling",
                )
        await session.commit()
    if finalized:
        log.info("finalize_settling_done", job="finalize_settling", finalized=finalized)


async def run_send_outcome_prompts(
    *, session_factory: Any = async_session_factory
) -> None:
    sms = get_sms_service()
    interval = timedelta(hours=settings.OUTCOME_PROMPT_INTERVAL_HOURS)
    sent = 0
    async with session_factory() as session:
        now = datetime.now(UTC)
        reservations = await res_crud.list_prompt_candidates(session, now, interval)
        for reservation in reservations:
            booking = await viewings_crud.get_active_booking_for_reservation(
                session, reservation.id
            )
            if booking is None or booking.window_id is None:
                continue
            window = await session.get(ViewingWindow, booking.window_id)
            if window is None:
                continue
            window_end = datetime.combine(
                window.window_date, window.time_to, tzinfo=UTC
            )
            if window_end >= now:
                continue
            buyer = await session.get(User, reservation.buyer_id)
            seller = await session.get(User, reservation.seller_id)
            message = "Просмотр прошёл — отметьте результат: состоялась ли сделка?"
            await _safe_sms(sms, buyer.phone if buyer else None, message)
            await _safe_sms(sms, seller.phone if seller else None, message)
            reservation.last_prompt_at = now
            sent += 1
        await session.commit()
    if sent:
        log.info("outcome_prompts_done", job="outcome_prompts", sent=sent)


async def run_expire_listings(*, session_factory: Any = async_session_factory) -> None:
    expired = 0
    async with session_factory() as session:
        stmt = select(Listing).where(
            col(Listing.status) == ListingStatus.active,
            col(Listing.expires_at) < datetime.now(UTC),
        )
        for listing in (await session.execute(stmt)).scalars().all():
            listing.status = ListingStatus.archived
            expired += 1
        await session.commit()
    if expired:
        log.info("expire_listings_done", job="expire_listings", expired=expired)


async def run_reconcile_deposits(
    *, session_factory: Any = async_session_factory
) -> None:
    deps = res_svc.default_deps()
    now = datetime.now(UTC)
    grace = timedelta(days=1)
    reconciled = 0
    async with session_factory() as session:
        pending = await res_crud.list_release_pending(session, now)
        for reservation in pending:
            if reservation.yk_payment_id is None:
                continue
            if reservation.hold_deadline + grace < now:
                reservation.deposit_released_at = now
                reconciled += 1
                continue
            try:
                await deps.yk.cancel_hold(
                    payment_id=reservation.yk_payment_id,
                    idempotence_key=f"{reservation.id}:release",
                )
            except DepositReleaseTerminalError:
                reservation.deposit_released_at = now
                reconciled += 1
                log.info(
                    "reconcile.terminal_release", reservation_id=str(reservation.id)
                )
                continue
            except DepositReleaseTransientError:
                log.warning("reconcile.deferred", reservation_id=str(reservation.id))
                continue
            reservation.deposit_released_at = datetime.now(UTC)
            reconciled += 1
        await session.commit()
    if reconciled:
        log.info(
            "reconcile_deposits_done", job="reconcile_deposits", reconciled=reconciled
        )


def _single_flight(
    job: Callable[[], Awaitable[None]],
    *,
    redis: Redis | None,
    key: str,
    ttl: int,
) -> Callable[[], Awaitable[None]]:
    @functools.wraps(job)
    async def wrapped() -> None:
        if redis is not None and not await redis.set(
            f"sched_lock:{key}", "1", ex=ttl, nx=True
        ):
            return
        await job()

    return wrapped


def build_scheduler(redis: Redis | None = None) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    rel = settings.SCHEDULER_RELEASE_EXPIRED_INTERVAL_SECONDS
    fin = settings.SCHEDULER_FINALIZE_SETTLING_INTERVAL_SECONDS
    pro = settings.SCHEDULER_OUTCOME_PROMPTS_INTERVAL_SECONDS
    exp = settings.SCHEDULER_EXPIRE_LISTINGS_INTERVAL_SECONDS
    scheduler.add_job(
        _single_flight(
            run_release_expired, redis=redis, key="release_expired", ttl=rel
        ),
        "interval",
        seconds=rel,
        id="release_expired",
        misfire_grace_time=rel // 2,
    )
    scheduler.add_job(
        _single_flight(
            run_finalize_settling, redis=redis, key="finalize_settling", ttl=fin
        ),
        "interval",
        seconds=fin,
        id="finalize_settling",
        misfire_grace_time=fin // 2,
    )
    scheduler.add_job(
        _single_flight(
            run_send_outcome_prompts, redis=redis, key="outcome_prompts", ttl=pro
        ),
        "interval",
        seconds=pro,
        id="outcome_prompts",
        misfire_grace_time=pro // 2,
    )
    scheduler.add_job(
        _single_flight(
            run_expire_listings, redis=redis, key="expire_listings", ttl=exp
        ),
        "interval",
        seconds=exp,
        id="expire_listings",
        misfire_grace_time=exp // 2,
    )
    rec = settings.SCHEDULER_RECONCILE_DEPOSITS_INTERVAL_SECONDS
    scheduler.add_job(
        _single_flight(
            run_reconcile_deposits, redis=redis, key="reconcile_deposits", ttl=rec
        ),
        "interval",
        seconds=rec,
        id="reconcile_deposits",
        misfire_grace_time=rec // 2,
    )
    return scheduler


def start_scheduler(app: FastAPI, redis: Redis) -> None:
    if not settings.SCHEDULER_ENABLED:
        app.state.scheduler = None
        return
    scheduler = build_scheduler(redis=redis)
    scheduler.start()
    app.state.scheduler = scheduler
    log.info("scheduler_started", jobs=[j.id for j in scheduler.get_jobs()])


def stop_scheduler(app: FastAPI) -> None:
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=True)
