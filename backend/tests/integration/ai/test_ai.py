from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_AUTH_BASE = "/api/v1/auth"
_AI_BASE = "/api/v1/ai"

_DEFAULT_EMAIL = "ai_user@example.org"
_DEFAULT_PWD = "TestPass123!"


async def _user_headers(client: AsyncClient, email: str = _DEFAULT_EMAIL):
    await client.post(
        f"{_AUTH_BASE}/register",
        json={
            "email": email,
            "password": _DEFAULT_PWD,
            "full_name": "AI User",
        },
    )
    tokens = (
        await client.post(
            f"{_AUTH_BASE}/login", json={"email": email, "password": _DEFAULT_PWD}
        )
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _parse_sse(raw: bytes):
    events = []
    for line in raw.decode().splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[len("data: ") :]))
            except json.JSONDecodeError:
                pass
    return events


async def test_chat_requires_auth(committed_client: AsyncClient):
    resp = await committed_client.post(f"{_AI_BASE}/chat", json={"message": "Hello"})
    assert resp.status_code == 401


async def test_chat_returns_sse_stream(committed_client: AsyncClient):
    headers = await _user_headers(committed_client)
    resp = await committed_client.post(
        f"{_AI_BASE}/chat",
        json={"message": "Привет"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    events = _parse_sse(resp.content)
    types = [e["type"] for e in events]
    assert "done" in types


async def test_chat_returns_token_events(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai2@example.org")
    resp = await committed_client.post(
        f"{_AI_BASE}/chat",
        json={"message": "Test message"},
        headers=headers,
    )
    events = _parse_sse(resp.content)
    token_events = [e for e in events if e["type"] == "token"]
    assert token_events, "expected at least one token event"
    text = "".join(e["content"] for e in token_events)
    assert len(text) > 0


async def test_chat_done_event_has_conversation_id(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai3@example.org")
    resp = await committed_client.post(
        f"{_AI_BASE}/chat",
        json={"message": "Hello"},
        headers=headers,
    )
    events = _parse_sse(resp.content)
    done = next((e for e in events if e["type"] == "done"), None)
    assert done is not None
    assert done["conversation_id"] is not None


async def test_chat_empty_message_returns_422(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai4@example.org")
    resp = await committed_client.post(
        f"{_AI_BASE}/chat",
        json={"message": ""},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_list_conversations_returns_empty_initially(
    committed_client: AsyncClient,
):
    headers = await _user_headers(committed_client, "ai5@example.org")
    resp = await committed_client.get(f"{_AI_BASE}/conversations", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


async def test_list_conversations_after_chat(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai6@example.org")
    await committed_client.post(
        f"{_AI_BASE}/chat", json={"message": "Hi"}, headers=headers
    )
    resp = await committed_client.get(f"{_AI_BASE}/conversations", headers=headers)
    assert resp.json()["count"] >= 1


async def test_get_conversation_detail(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai7@example.org")
    chat_resp = await committed_client.post(
        f"{_AI_BASE}/chat", json={"message": "Hello"}, headers=headers
    )
    events = _parse_sse(chat_resp.content)
    done = next(e for e in events if e["type"] == "done")
    conv_id = done["conversation_id"]

    resp = await committed_client.get(
        f"{_AI_BASE}/conversations/{conv_id}", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "messages" in body
    assert len(body["messages"]) >= 1


async def test_delete_conversation(committed_client: AsyncClient):
    headers = await _user_headers(committed_client, "ai8@example.org")
    chat_resp = await committed_client.post(
        f"{_AI_BASE}/chat", json={"message": "Delete me"}, headers=headers
    )
    events = _parse_sse(chat_resp.content)
    done = next(e for e in events if e["type"] == "done")
    conv_id = done["conversation_id"]

    del_resp = await committed_client.delete(
        f"{_AI_BASE}/conversations/{conv_id}", headers=headers
    )
    assert del_resp.status_code == 204

    get_resp = await committed_client.get(
        f"{_AI_BASE}/conversations/{conv_id}", headers=headers
    )
    assert get_resp.status_code == 404
