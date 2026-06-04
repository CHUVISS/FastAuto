from __future__ import annotations

import logging
import os
import sys
from typing import Any

import orjson
import structlog
from structlog.stdlib import ProcessorFormatter

log = structlog.get_logger(__name__)


def _add_worker_pid(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    event_dict["pid"] = os.getpid()
    return event_dict


def configure_logging(settings: Any) -> None:
    is_dev = settings.ENVIRONMENT == "local"
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        _add_worker_pid,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if not is_dev:
        shared_processors.append(structlog.processors.ExceptionRenderer())

    structlog.configure(
        processors=[*shared_processors, ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    renderer: Any = (
        structlog.dev.ConsoleRenderer()
        if is_dev
        else structlog.processors.JSONRenderer(serializer=orjson.dumps)
    )

    formatter = ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)

    for name in (
        "sqlalchemy.engine",
        "granian",
        "granian.access",
        "apscheduler.executors",
        "apscheduler.scheduler",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def log_startup(settings: Any) -> None:
    log.info(
        "application_started",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        storage=settings.STORAGE_BACKEND,
        scheduler=settings.SCHEDULER_ENABLED,
        sentry=bool(settings.SENTRY_DSN),
        db_driver=settings.DB_DRIVER,
    )
