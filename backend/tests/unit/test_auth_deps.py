import pytest

from app.api.dependencies import auth as auth_deps
from app.api.dependencies.auth import _user_from_cache_dict, _user_to_cache_dict
from app.models.users import User, UserRole

pytestmark = pytest.mark.unit


def test_cache_roundtrip_preserves_phone_and_role():
    u = User(
        full_name="A B",
        email="a@b.com",
        hashed_password="x",
        role=UserRole.moderator,
        phone="79161234567",
        phone_verified=True,
        phone_visible=False,
    )
    restored = _user_from_cache_dict(_user_to_cache_dict(u))
    assert restored.role == UserRole.moderator
    assert restored.phone == "79161234567"
    assert restored.phone_verified is True
    assert restored.phone_visible is False


def test_moderator_user_dependency_exists():
    assert hasattr(auth_deps, "ModeratorUser")
    assert "ModeratorUser" in auth_deps.__all__
