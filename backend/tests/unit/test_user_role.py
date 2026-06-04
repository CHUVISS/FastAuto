import pytest

from app.models.users import User, UserRole

pytestmark = pytest.mark.unit


def test_moderator_role_exists():
    assert UserRole.moderator.value == "moderator"


def test_role_set_contains_all_roles():
    values = {r.value for r in UserRole}
    assert values == {"user", "support", "moderator", "manager", "admin"}


def test_user_has_phone_fields_defaults():
    u = User(email="a@b.com", hashed_password="x", full_name="A B")
    assert u.phone is None
    assert u.phone_verified is False
    assert u.phone_visible is True
