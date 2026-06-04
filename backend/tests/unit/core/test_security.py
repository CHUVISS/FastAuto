from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_hash_password_returns_argon2_hash():
    hashed = await hash_password("mysecretpassword")
    assert hashed.startswith("$argon2")


@pytest.mark.asyncio
async def test_hash_password_different_for_same_input():
    hashed1 = await hash_password("samepassword")
    hashed2 = await hash_password("samepassword")
    assert hashed1 != hashed2


@pytest.mark.asyncio
async def test_verify_password_success():
    password = "correcthorsebatterystaple"
    hashed = await hash_password(password)
    assert await verify_password(password, hashed) is True


@pytest.mark.asyncio
async def test_verify_password_failure_wrong_password():
    hashed = await hash_password("rightpassword")
    assert await verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_verify_password_handles_invalid_hash_gracefully():
    from pwdlib.exceptions import UnknownHashError

    with pytest.raises(UnknownHashError):
        await verify_password("anypassword", "not-a-valid-hash-at-all")


@pytest.mark.asyncio
async def test_hash_password_async_does_not_block_loop():
    passwords = [f"password{i}" for i in range(5)]
    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[hash_password(p) for p in passwords])
    elapsed = asyncio.get_event_loop().time() - start

    assert len(results) == 5
    assert all(h.startswith("$argon2") for h in results)
    assert elapsed < 5.0


def test_create_access_token_contains_required_claims():
    token = create_access_token(subject="user-123")
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert payload["sub"] == "user-123"
    assert payload["type"] == settings.TOKEN_TYPE_ACCESS
    assert "iat" in payload
    assert "exp" in payload


def test_create_refresh_token_uses_refresh_secret():
    token = create_refresh_token(subject="user-456")

    payload = jwt.decode(
        token,
        settings.REFRESH_SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    assert payload["sub"] == "user-456"
    assert payload["type"] == settings.TOKEN_TYPE_REFRESH

    if settings.SECRET_KEY != settings.REFRESH_SECRET_KEY:
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )


def test_create_token_uses_default_expire_when_omitted():
    before = datetime.now(UTC)
    token = create_access_token(subject="u1")
    after = datetime.now(UTC)

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_min = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expected_max = after + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    assert (
        expected_min - timedelta(seconds=5)
        <= exp
        <= expected_max + timedelta(seconds=5)
    )


def test_create_token_uses_custom_expire_delta():
    before = datetime.now(UTC)
    token = create_access_token(subject="u2", expires_delta=timedelta(seconds=60))
    after = datetime.now(UTC)

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected_min = before + timedelta(seconds=60)
    expected_max = after + timedelta(seconds=60)

    assert (
        expected_min - timedelta(seconds=5)
        <= exp
        <= expected_max + timedelta(seconds=5)
    )


def test_verify_token_returns_subject_and_iat_on_success():
    token = create_access_token(subject="abc-123")
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)

    assert result is not None
    sub, iat = result
    assert sub == "abc-123"
    assert isinstance(sub, str)
    assert isinstance(iat, int)


def test_verify_token_rejects_wrong_type():
    token = create_refresh_token(subject="user-789")
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)
    assert result is None


def test_verify_token_rejects_alg_none():
    payload = {
        "sub": "attacker",
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": settings.TOKEN_TYPE_ACCESS,
    }
    token = jwt.encode(payload, "", algorithm="none")
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)
    assert result is None


def test_verify_token_rejects_expired():
    token = create_access_token(
        subject="u-expired", expires_delta=timedelta(seconds=-1)
    )
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)
    assert result is None


def test_verify_token_rejects_missing_required_claim():
    payload = {
        "sub": "u-no-iat",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": settings.TOKEN_TYPE_ACCESS,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)
    assert result is None


def test_verify_token_rejects_malformed():
    result = verify_token("not-a-token")
    assert result is None


def test_verify_token_rejects_wrong_signature():
    token = jwt.encode(
        {
            "sub": "u-badsig",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": datetime.now(UTC) + timedelta(minutes=5),
            "type": settings.TOKEN_TYPE_ACCESS,
        },
        "completely-wrong-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
    )
    result = verify_token(token, expected_type=settings.TOKEN_TYPE_ACCESS)
    assert result is None
