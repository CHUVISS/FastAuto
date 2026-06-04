import pytest

from app.models.tickets import TicketMessage, TicketStatus, TicketType

pytestmark = pytest.mark.unit


def test_ticket_type_values():
    assert {t.value for t in TicketType} == {
        "purchase_dispute",
        "listing_report",
        "moderation_appeal",
        "support_inquiry",
    }


def test_ticket_status_values():
    assert {s.value for s in TicketStatus} == {
        "open",
        "in_progress",
        "resolved",
        "closed",
    }


def test_ticket_message_cascade_fk():
    fk = next(iter(TicketMessage.__table__.columns["ticket_id"].foreign_keys))
    assert fk.ondelete == "CASCADE"
