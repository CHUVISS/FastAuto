from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.models.users import UserRole
from app.schemas.ai import AiChatRequest
from app.schemas.users import ProfileUpdate, UserCreate, UserRegister

pytestmark = pytest.mark.unit


def test_profile_update_valid_phone():
    p = ProfileUpdate(phone="79991234567")
    assert p.phone == "79991234567"


def test_profile_update_none_phone_ok():
    p = ProfileUpdate(phone=None)
    assert p.phone is None


def test_profile_update_invalid_phone_raises():
    with pytest.raises(ValidationError):
        ProfileUpdate(phone="not-a-phone!!!")


def test_profile_update_all_none_ok():
    p = ProfileUpdate()
    assert p.full_name is None and p.phone is None


def test_ai_chat_request_min_length_ok():
    r = AiChatRequest(message="x")
    assert r.message == "x"


def test_ai_chat_request_empty_raises():
    with pytest.raises(ValidationError):
        AiChatRequest(message="")


def test_ai_chat_request_too_long_raises():
    with pytest.raises(ValidationError):
        AiChatRequest(message="x" * 4001)


def test_ai_chat_request_max_length_ok():
    r = AiChatRequest(message="x" * 4000)
    assert len(r.message) == 4000


def test_ai_chat_request_optional_conversation_id():
    r = AiChatRequest(message="hi", conversation_id=None)
    assert r.conversation_id is None
    uid = uuid.uuid4()
    r2 = AiChatRequest(message="hi", conversation_id=uid)
    assert r2.conversation_id == uid


def test_user_create_valid():
    u = UserCreate(
        email="a@b.com", password="Pass123!", full_name="A B", role=UserRole.manager
    )
    assert u.role == UserRole.manager


def test_user_register_valid():
    r = UserRegister(email="a@b.com", password="Pass123!", full_name="A B")
    assert r.email == "a@b.com"
