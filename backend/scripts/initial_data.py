import asyncio

import structlog

from app.core.config import settings
from app.core.db import init_db
from app.core.log import configure_logging

configure_logging(settings)
log = structlog.get_logger(__name__)


def main() -> None:
    log.info("creating_initial_data")
    asyncio.run(init_db())
    log.info("initial_data_created")


if __name__ == "__main__":
    main()
