from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.utils.pagination import PaginationParams
from app.utils.request import get_client_ip

pytestmark = pytest.mark.unit


def test_pagination_defaults():
    p = PaginationParams(skip=0, limit=20)
    assert p.skip == 0
    assert p.limit == 20


def test_pagination_skip_zero_ok():
    p = PaginationParams(skip=0, limit=10)
    assert p.skip == 0


def test_pagination_skip_positive_ok():
    p = PaginationParams(skip=50, limit=5)
    assert p.skip == 50


def _request(host="1.2.3.4", forwarded_for=None):
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = host
    req.headers = {}
    if forwarded_for is not None:
        req.headers = {"X-Forwarded-For": forwarded_for}
    return req


def test_get_client_ip_uses_direct_host_when_not_proxied(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "TRUST_PROXY_HEADERS", False)
    req = _request(host="10.0.0.1")
    assert get_client_ip(req) == "10.0.0.1"


def test_get_client_ip_reads_forwarded_for_when_trusted(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "TRUST_PROXY_HEADERS", True)
    req = _request(host="127.0.0.1", forwarded_for="203.0.113.5, 10.0.0.1")
    assert get_client_ip(req) == "203.0.113.5"


def test_get_client_ip_falls_back_to_host_when_trusted_but_no_header(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "TRUST_PROXY_HEADERS", True)
    req = _request(host="10.0.0.1")
    assert get_client_ip(req) == "10.0.0.1"


def test_get_client_ip_returns_unknown_when_no_client(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "TRUST_PROXY_HEADERS", False)
    req = MagicMock()
    req.client = None
    req.headers = {}
    assert get_client_ip(req) == "unknown"


def test_get_client_ip_strips_whitespace_in_forwarded_for(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "TRUST_PROXY_HEADERS", True)
    req = _request(forwarded_for="  55.66.77.88  , 10.0.0.1")
    assert get_client_ip(req) == "55.66.77.88"
