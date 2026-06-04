import asyncio
import logging

import asyncpg
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.core.log import configure_logging

configure_logging(settings)
log = logging.getLogger(__name__)

MAX_TRIES = 60 * 5
WAIT_SECONDS = 1

_HOST = settings.PGBOUNCER_HOST if settings.USE_PGBOUNCER else settings.POSTGRES_SERVER
_PORT = settings.PGBOUNCER_PORT if settings.USE_PGBOUNCER else settings.POSTGRES_PORT


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(log, logging.INFO),  # type: ignore[arg-type]
    after=after_log(log, logging.WARNING),  # type: ignore[arg-type]
)
async def check() -> None:
    conn = await asyncpg.connect(
        host=_HOST,
        port=_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        ssl=False,
    )
    await conn.close()


if __name__ == "__main__":
    log.info("Ожидание базы данных…")
    asyncio.run(check())
    log.info("База данных готова.")
