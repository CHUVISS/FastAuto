import pytest

from app.crud import tickets as ticket_crud
from app.models.tickets import Ticket, TicketMessage, TicketStatus, TicketType

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_ticket_with_message(db_session, regular_user):
    ticket = await ticket_crud.create(
        db_session,
        Ticket(
            type=TicketType.support_inquiry, creator_id=regular_user.id, title="Help"
        ),
    )
    await db_session.flush()
    await ticket_crud.add_message(
        db_session,
        TicketMessage(ticket_id=ticket.id, sender_id=regular_user.id, body="Hello"),
    )
    await db_session.flush()
    msgs = await ticket_crud.list_messages(db_session, ticket.id)
    assert [m.body for m in msgs] == ["Hello"]


@pytest.mark.asyncio
async def test_list_filters_and_my(db_session, regular_user, admin_user):
    await ticket_crud.create(
        db_session,
        Ticket(
            type=TicketType.listing_report,
            creator_id=regular_user.id,
            title="A",
            status=TicketStatus.open,
        ),
    )
    await ticket_crud.create(
        db_session,
        Ticket(
            type=TicketType.support_inquiry,
            creator_id=admin_user.id,
            title="B",
            status=TicketStatus.closed,
        ),
    )
    await db_session.flush()

    open_reports = await ticket_crud.list_all(
        db_session, type=TicketType.listing_report, status=TicketStatus.open
    )
    assert len(open_reports) == 1
    mine = await ticket_crud.list_for_user(db_session, regular_user.id)
    assert {t.title for t in mine} == {"A"}
