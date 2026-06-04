from __future__ import annotations

from fastapi import Request

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
