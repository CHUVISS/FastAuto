from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.users import create_user
from app.models.users import UserRole
from app.schemas.users import UserCreate
from app.services.ai import ai_service
from tests.fixtures.ollama import MockOllamaResponse

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def ai_session(pg_container, engine):
    from sqlalchemy.ext.asyncio import create_async_engine

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as s:
            yield s
        await trans.rollback()
    await eng.dispose()


def _user_create():
    return UserCreate(
        email=f"u{uuid.uuid4().hex[:8]}@example.org",
        password="TestPass123!",
        full_name="AI Test User",
        role=UserRole.user,
    )


@pytest_asyncio.fixture
async def ai_user(ai_session):
    u = await create_user(ai_session, _user_create())
    await ai_session.flush()
    return u


async def _collect(gen):
    return [chunk async for chunk in gen]


def _parse_sse(chunks):
    out = []
    for chunk in chunks:
        for line in chunk.splitlines():
            if line.startswith("data: "):
                out.append(json.loads(line[len("data: ") :]))
    return out


def _tool_call_obj(name, arguments):
    tc = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


async def test_stream_rejects_injection_attempt(monkeypatch):
    monkeypatch.setattr(ai_service, "sanitize", lambda text: (text, True))

    session = AsyncMock()
    chunks = await _collect(
        ai_service.stream_ai_response(
            "anything", uuid.uuid4(), session, conversation_id=None
        )
    )
    events = _parse_sse(chunks)

    types = [e["type"] for e in events]
    assert types == ["token", "done"]

    rejection = events[0]["content"].lower()
    assert "не могу" in rejection or "автомоб" in rejection

    session.commit.assert_not_called()
    session.execute.assert_not_called()


async def test_stream_creates_conversation_for_new_user(
    ai_session, ai_user, monkeypatch
):
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(
        return_value=MockOllamaResponse(content="Привет, чем помочь?")
    )
    monkeypatch.setattr(ai_service, "_get_client", lambda: fake_client)

    chunks = await _collect(
        ai_service.stream_ai_response(
            "Здравствуйте", ai_user.id, ai_session, conversation_id=None
        )
    )
    events = _parse_sse(chunks)
    types = [e["type"] for e in events]
    assert types[-1] == "done"
    token_events = [e for e in events if e["type"] == "token"]
    assert token_events, "expected at least one token event"
    streamed = "".join(t["content"] for t in token_events)
    assert "Привет" in streamed

    done_event = next(e for e in events if e["type"] == "done")
    assert done_event["conversation_id"] is not None
    uuid.UUID(done_event["conversation_id"])


async def test_stream_handles_ollama_timeout(ai_session, ai_user, monkeypatch):
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(side_effect=TimeoutError())
    monkeypatch.setattr(ai_service, "_get_client", lambda: fake_client)

    chunks = await _collect(
        ai_service.stream_ai_response(
            "сколько стоит camry?",
            ai_user.id,
            ai_session,
            conversation_id=None,
        )
    )
    events = _parse_sse(chunks)
    err_events = [e for e in events if e["type"] == "error"]
    assert err_events, f"expected an error event, got: {events}"
    msg = err_events[0]["message"].lower()
    assert "ожидан" in msg or "истек" in msg


async def test_stream_max_tool_rounds_safety(monkeypatch):
    tool_call = _tool_call_obj("search_listings", {"mark": "Toyota"})
    tool_response = MockOllamaResponse(content="", tool_calls=[tool_call])

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=tool_response)
    monkeypatch.setattr(ai_service, "_get_client", lambda: fake_client)

    async def _fake_execute_tool(*_args, **_kwargs):
        return json.dumps({"found": 0, "listings": []}), None

    monkeypatch.setattr(ai_service, "execute_tool", _fake_execute_tool)

    mock_conv = MagicMock()
    mock_conv.id = uuid.uuid4()
    mock_msg = MagicMock()
    mock_msg.id = uuid.uuid4()
    monkeypatch.setattr(
        ai_service, "load_or_create_conversation", AsyncMock(return_value=mock_conv)
    )
    monkeypatch.setattr(ai_service, "load_history", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_service, "save_message", AsyncMock(return_value=mock_msg))
    monkeypatch.setattr(ai_service, "save_tool_call", AsyncMock(return_value=None))
    monkeypatch.setattr(ai_service, "touch_conversation", AsyncMock(return_value=None))

    session = AsyncMock()
    chunks = await _collect(
        ai_service.stream_ai_response(
            "найди машину", uuid.uuid4(), session, conversation_id=None
        )
    )
    events = _parse_sse(chunks)

    assert fake_client.chat.await_count == settings.AI_MAX_TOOL_CALL_ROUNDS
    assert events[-1]["type"] == "done"


async def test_stream_strips_think_tags(ai_session, ai_user, monkeypatch):
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(
        return_value=MockOllamaResponse(content="<think>hidden</think>visible")
    )
    monkeypatch.setattr(ai_service, "_get_client", lambda: fake_client)

    chunks = await _collect(
        ai_service.stream_ai_response(
            "test", ai_user.id, ai_session, conversation_id=None
        )
    )
    events = _parse_sse(chunks)
    token_events = [e for e in events if e["type"] == "token"]
    streamed = "".join(t["content"] for t in token_events)
    assert "visible" in streamed
    assert "hidden" not in streamed
    assert "<think>" not in streamed


async def test_stream_logs_db_setup_failure_gracefully(monkeypatch):
    failing_session = AsyncMock()
    failing_session.execute = AsyncMock(side_effect=RuntimeError("db boom"))
    failing_session.add = MagicMock()

    fake_client = MagicMock()
    fake_client.chat = AsyncMock()
    monkeypatch.setattr(ai_service, "_get_client", lambda: fake_client)

    chunks = await _collect(
        ai_service.stream_ai_response(
            "hi", uuid.uuid4(), failing_session, conversation_id=None
        )
    )
    events = _parse_sse(chunks)
    err_events = [e for e in events if e["type"] == "error"]
    assert err_events, f"expected error event, got: {events}"
    msg = err_events[0]["message"].lower()
    assert "сохранени" in msg or "диалог" in msg

    fake_client.chat.assert_not_called()
