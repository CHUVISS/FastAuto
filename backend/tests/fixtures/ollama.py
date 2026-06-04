from __future__ import annotations

from typing import Any


class MockOllamaResponse:
    def __init__(self, content: str = "Test response", tool_calls: list | None = None):
        self.message = MockMessage(content=content, tool_calls=tool_calls)


class MockMessage:
    def __init__(self, content: str, tool_calls: list | None = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.role = "assistant"


class MockOllamaClient:
    def __init__(self, responses: list[Any] | None = None):
        self._responses = responses or [MockOllamaResponse("Hello from mock")]
        self._idx = 0
        self.calls: list[dict] = []

    def set_responses(self, responses: list[Any]) -> None:
        self._responses = responses
        self._idx = 0

    async def chat(self, *, model: str, messages: list, tools=None, **_kwargs):
        self.calls.append({"model": model, "messages": messages, "tools": tools})
        if self._idx < len(self._responses):
            resp = self._responses[self._idx]
            self._idx += 1
            return resp
        return MockOllamaResponse("Default mock response")
