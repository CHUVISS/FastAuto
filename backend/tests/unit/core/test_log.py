from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
import structlog
from structlog.stdlib import ProcessorFormatter

pytestmark = pytest.mark.unit


def _settings(**kw):
    base = {"ENVIRONMENT": "local", "LOG_LEVEL": "INFO"}
    return SimpleNamespace(**{**base, **kw})


def test_configure_logging_local_uses_console_renderer():
    from app.core.log import configure_logging

    configure_logging(_settings(ENVIRONMENT="local"))

    root = logging.getLogger()
    assert len(root.handlers) == 1
    fmt = root.handlers[0].formatter
    assert isinstance(fmt, ProcessorFormatter)
    assert isinstance(fmt.processors[-1], structlog.dev.ConsoleRenderer)


def test_configure_logging_production_uses_json_renderer():
    from app.core.log import configure_logging

    configure_logging(_settings(ENVIRONMENT="production"))

    root = logging.getLogger()
    fmt = root.handlers[0].formatter
    assert isinstance(fmt, ProcessorFormatter)
    assert isinstance(fmt.processors[-1], structlog.processors.JSONRenderer)


def test_configure_logging_suppresses_sqlalchemy():
    from app.core.log import configure_logging

    configure_logging(_settings())

    assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING


def test_configure_logging_suppresses_granian():
    from app.core.log import configure_logging

    configure_logging(_settings())

    assert logging.getLogger("granian").level == logging.WARNING
    assert logging.getLogger("granian.access").level == logging.WARNING


def test_configure_logging_sets_root_level_from_setting():
    from app.core.log import configure_logging

    configure_logging(_settings(LOG_LEVEL="DEBUG"))

    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_is_idempotent():
    from app.core.log import configure_logging

    configure_logging(_settings())
    configure_logging(_settings())

    assert len(logging.getLogger().handlers) == 1
