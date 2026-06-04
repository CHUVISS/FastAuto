import pytest

from app.api.routes.reservations import _refund_delay_seconds

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "count,expected",
    [(0, 0), (1, 3600), (2, 21600), (3, 86400), (4, 259200), (10, 259200)],
)
def test_refund_delay_tier_picks_correct_value(count, expected):
    assert _refund_delay_seconds(count) == expected
