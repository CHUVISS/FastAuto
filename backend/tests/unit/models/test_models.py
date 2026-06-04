from __future__ import annotations

import pytest

from app.models.listings import Condition, ListingStatus
from app.models.reservations import ReservationStatus
from app.models.tickets import TicketStatus, TicketType
from app.models.users import UserRole, UserStatus

pytestmark = pytest.mark.unit


def test_user_role_values():
    assert set(UserRole) == {"admin", "manager", "support", "moderator", "user"}


def test_user_status_values():
    assert set(UserStatus) == {"active", "inactive", "banned"}


def test_listing_status_values():
    assert set(ListingStatus) == {
        "draft",
        "pending_review",
        "active",
        "reserved",
        "sold",
        "archived",
    }


def test_condition_values():
    assert set(Condition) == {"excellent", "good", "fair", "poor"}


def test_reservation_status_values():
    assert set(ReservationStatus) == {
        "pending_payment",
        "active",
        "settling",
        "completed",
        "cancelled",
    }


def test_ticket_status_values():
    assert set(TicketStatus) == {"open", "in_progress", "resolved", "closed"}


def test_ticket_type_values():
    assert "support_inquiry" in set(TicketType)
    assert "purchase_dispute" in set(TicketType)


def test_user_role_str_value():
    assert UserRole.admin == "admin"
    assert str(UserRole.user) == "user"


def test_listing_status_str_value():
    assert ListingStatus.active == "active"
    assert str(ListingStatus.sold) == "sold"
