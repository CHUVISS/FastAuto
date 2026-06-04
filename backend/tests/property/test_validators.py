from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st
from pydantic import ValidationError

pytestmark = pytest.mark.unit


@given(st.from_regex(r"^\+?[78][0-9]{10}$", fullmatch=True))
@h_settings(max_examples=50)
def test_valid_russian_phone_accepted(phone):
    from app.schemas.users import ProfileUpdate

    result = ProfileUpdate(phone=phone)
    assert result.phone is not None
    assert result.phone.startswith("7")
    assert len(result.phone) == 11


@given(
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz@#$%^&*!",
        min_size=7,
        max_size=20,
    )
)
@h_settings(max_examples=30)
def test_phone_with_letters_rejected(phone):
    from app.schemas.users import ProfileUpdate

    with pytest.raises(ValidationError):
        ProfileUpdate(phone=phone)


@given(st.text(min_size=1, max_size=5))
@h_settings(max_examples=30)
def test_phone_too_short_rejected(phone):
    from app.schemas.users import ProfileUpdate

    with pytest.raises(ValidationError):
        ProfileUpdate(phone=phone)


def test_phone_none_accepted():
    from app.schemas.users import ProfileUpdate

    assert ProfileUpdate(phone=None).phone is None


@given(st.text(min_size=1, max_size=4000))
@h_settings(max_examples=50)
def test_ai_message_valid_length_accepted(message):
    from app.schemas.ai import AiChatRequest

    req = AiChatRequest(message=message)
    assert 1 <= len(req.message) <= 4000


@given(st.text(min_size=4001, max_size=4100))
@h_settings(max_examples=30)
def test_ai_message_too_long_rejected(message):
    from app.schemas.ai import AiChatRequest

    with pytest.raises(ValidationError):
        AiChatRequest(message=message)


def test_ai_message_empty_rejected():
    from app.schemas.ai import AiChatRequest

    with pytest.raises(ValidationError):
        AiChatRequest(message="")
