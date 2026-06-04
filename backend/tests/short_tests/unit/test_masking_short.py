from __future__ import annotations

import pytest

from app.utils.masking import mask_tail

pytestmark = pytest.mark.unit


def test_mask_tail_default_keeps_last_two_chars():
    assert mask_tail("WBA12345678901234") == "***************34"


def test_mask_tail_none_returns_none_and_short_values_fully_masked():
    assert mask_tail(None) is None
    assert mask_tail("A") == "*"
    assert mask_tail("AB") == "**"
    assert mask_tail("ABCDEF", keep=3) == "***DEF"
