import pytest

from app.utils.units import cc_to_litres

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "cc,expected",
    [
        ("2977", "2.977"),
        ("3179", "3.179"),
        ("3664", "3.664"),
        ("1998", "1.998"),
        ("3000", "3"),  # exact thousands → no trailing zeros, no rounding
        ("500", "0.5"),
        ("99", "0.099"),
    ],
)
def test_cc_to_litres_shifts_decimal_without_rounding(cc, expected):
    assert cc_to_litres(cc) == expected


def test_cc_to_litres_passthrough_for_none_and_non_numeric():
    assert cc_to_litres(None) is None
    assert cc_to_litres("") == ""
    assert cc_to_litres("n/a") == "n/a"
