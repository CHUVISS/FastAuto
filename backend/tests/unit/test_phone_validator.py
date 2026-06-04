from __future__ import annotations

import pytest

from app.schemas.common import normalize_russian_phone

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("79991234567", "79991234567"),
        ("+79991234567", "79991234567"),
        ("89991234567", "79991234567"),
        ("+7 (999) 123-45-67", "79991234567"),
        ("  +7 999 123 45 67  ", "79991234567"),
    ],
)
def test_normalize_accepts_common_formats(raw: str, expected: str) -> None:
    assert normalize_russian_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "abc",
        "12345",
        "+1234567890",
        "9991234567",
        "799912345678",
        "+1 (999) 123-45-67",
    ],
)
def test_normalize_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_russian_phone(raw)


def test_normalize_passes_none() -> None:
    assert normalize_russian_phone(None) is None
