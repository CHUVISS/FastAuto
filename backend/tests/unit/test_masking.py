import pytest

from app.utils.masking import mask_tail

pytestmark = pytest.mark.unit


def test_mask_tail_keeps_last_two():
    assert mask_tail("WVWZZZ1KZ6W123456") == "***************56"


def test_mask_tail_none():
    assert mask_tail(None) is None


def test_mask_tail_short_values_fully_masked():
    assert mask_tail("X") == "*"
    assert mask_tail("AB") == "**"


def test_mask_tail_custom_keep():
    assert mask_tail("ABCDEF", keep=3) == "***DEF"
