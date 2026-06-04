from __future__ import annotations

from typing import Any

import structlog

log = structlog.get_logger(__name__)


def init_sentry(settings: Any) -> None:
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        release=settings.SENTRY_RELEASE or None,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            AsyncioIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
    )
    log.info(
        "sentry_initialized",
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        release=settings.SENTRY_RELEASE or "<unset>",
    )
