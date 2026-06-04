from __future__ import annotations

import threading
from dataclasses import dataclass
from time import monotonic


@dataclass(slots=True)
class _Entry:
    body: bytes
    expires_at: float


_STORE: dict[str, _Entry] = {}
_LOCK = threading.Lock()


def get(key: str) -> bytes | None:
    entry = _STORE.get(key)
    if entry is None:
        return None
    if entry.expires_at < monotonic():
        with _LOCK:
            _STORE.pop(key, None)
        return None
    return entry.body


def set_(key: str, body: bytes, ttl: int) -> None:
    _STORE[key] = _Entry(body=body, expires_at=monotonic() + ttl)


def clear() -> None:
    with _LOCK:
        _STORE.clear()


def size() -> int:
    return len(_STORE)
