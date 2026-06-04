from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select

from app.crud.users import create_user
from app.models.ai import AiConversation, AiMessage, AiMessageRole
from app.models.users import UserRole
from app.schemas.users import UserCreate
from app.services.ai.ai_history import (
    delete_conversation,
    load_history,
    load_or_create_conversation,
    save_message,
    touch_conversation,
)

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def ai_engine(pg_container, engine):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def ai_session(ai_engine):
    async with ai_engine.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as s:
            yield s
        await trans.rollback()


def _user_create(role=UserRole.user):
    return UserCreate(
        email=f"u{uuid.uuid4().hex[:8]}@example.org",
        password="TestPass123!",
        full_name=f"Test {role.value.title()}",
        role=role,
    )


@pytest_asyncio.fixture
async def user_a(ai_session):
    u = await create_user(ai_session, _user_create(UserRole.user))
    await ai_session.flush()
    return u


@pytest_asyncio.fixture
async def user_b(ai_session):
    u = await create_user(ai_session, _user_create(UserRole.user))
    await ai_session.flush()
    return u


async def test_load_or_create_creates_new_conversation_for_none_id(ai_session, user_a):
    conv = await load_or_create_conversation(ai_session, user_a.id, None, "Hello there")
    assert conv.id is not None
    assert conv.user_id == user_a.id
    assert conv.title == "Hello there"


async def test_load_or_create_returns_existing_for_same_user(ai_session, user_a):
    first = await load_or_create_conversation(ai_session, user_a.id, None, "Initial")
    await ai_session.flush()

    second = await load_or_create_conversation(
        ai_session, user_a.id, first.id, "Different first message"
    )
    assert second.id == first.id
    assert second.title == "Initial"


async def test_load_or_create_creates_new_for_different_user(
    ai_session, user_a, user_b
):
    conv_a = await load_or_create_conversation(
        ai_session, user_a.id, None, "Owned by A"
    )
    await ai_session.flush()

    conv_b = await load_or_create_conversation(
        ai_session, user_b.id, conv_a.id, "Owned by B"
    )
    assert conv_b.id != conv_a.id
    assert conv_b.user_id == user_b.id


async def test_load_or_create_truncates_long_title(ai_session, user_a):
    long_message = "a" * 200
    conv = await load_or_create_conversation(ai_session, user_a.id, None, long_message)
    assert conv.title is not None
    assert conv.title.endswith("...")
    assert len(conv.title) == 63


async def test_load_history_excludes_tool_messages(ai_session, user_a):
    conv = await load_or_create_conversation(ai_session, user_a.id, None, "history")
    await save_message(ai_session, conv.id, AiMessageRole.user, "user msg")
    await save_message(ai_session, conv.id, AiMessageRole.assistant, "assistant msg")
    await save_message(ai_session, conv.id, AiMessageRole.tool, "tool result blob")
    await ai_session.flush()

    history = await load_history(ai_session, conv.id)
    contents = [m["content"] for m in history]
    roles = [m["role"] for m in history]

    assert "tool result blob" not in contents
    assert AiMessageRole.tool not in roles
    assert "user msg" in contents
    assert "assistant msg" in contents


async def test_load_history_returns_chronological(ai_session, user_a):
    conv = await load_or_create_conversation(
        ai_session, user_a.id, None, "chronological"
    )
    await save_message(ai_session, conv.id, AiMessageRole.user, "first")
    await asyncio.sleep(0.01)
    await save_message(ai_session, conv.id, AiMessageRole.assistant, "second")
    await asyncio.sleep(0.01)
    await save_message(ai_session, conv.id, AiMessageRole.user, "third")
    await ai_session.flush()

    history = await load_history(ai_session, conv.id)
    contents = [m["content"] for m in history]
    assert contents == ["first", "second", "third"]


async def test_save_message_persists_with_metadata(ai_session, user_a):
    conv = await load_or_create_conversation(ai_session, user_a.id, None, "metadata")
    saved = await save_message(
        ai_session,
        conv.id,
        AiMessageRole.assistant,
        "answer",
        model_name="qwen-test:1b",
        input_tokens=12,
        output_tokens=34,
    )
    await ai_session.flush()

    result = await ai_session.execute(select(AiMessage).where(AiMessage.id == saved.id))
    msg = result.scalars().one()
    assert msg.model_name == "qwen-test:1b"
    assert msg.input_tokens == 12
    assert msg.output_tokens == 34
    assert msg.content == "answer"


async def test_touch_conversation_updates_last_message_at(ai_session, user_a):
    conv = await load_or_create_conversation(ai_session, user_a.id, None, "touch")
    await ai_session.flush()

    past = datetime.now(UTC) - timedelta(hours=1)
    conv.last_message_at = past
    ai_session.add(conv)
    await ai_session.flush()

    before = conv.last_message_at
    await touch_conversation(ai_session, conv)
    await ai_session.flush()

    assert conv.last_message_at > before


async def test_delete_conversation_returns_true_and_cascades(ai_session, user_a):
    conv = await load_or_create_conversation(ai_session, user_a.id, None, "delete")
    await save_message(ai_session, conv.id, AiMessageRole.user, "to be cascaded")
    await ai_session.flush()

    ok = await delete_conversation(ai_session, conv.id, user_a.id)
    assert ok is True

    msg_result = await ai_session.execute(
        select(AiMessage).where(AiMessage.conversation_id == conv.id)
    )
    assert msg_result.scalars().first() is None

    conv_result = await ai_session.execute(
        select(AiConversation).where(AiConversation.id == conv.id)
    )
    assert conv_result.scalars().first() is None


async def test_delete_conversation_returns_false_for_other_user(
    ai_session, user_a, user_b
):
    conv = await load_or_create_conversation(
        ai_session, user_a.id, None, "other-user-delete"
    )
    await ai_session.flush()

    ok = await delete_conversation(ai_session, conv.id, user_b.id)
    assert ok is False

    result = await ai_session.execute(
        select(AiConversation).where(AiConversation.id == conv.id)
    )
    assert result.scalars().first() is not None
