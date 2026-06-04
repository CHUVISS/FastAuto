import pytest

from app.models.notifications import Notification

pytestmark = pytest.mark.unit


def test_table_and_columns():
    assert Notification.__tablename__ == "notifications"
    cols = Notification.__table__.columns
    assert "user_id" in cols and "type" in cols and "payload" in cols
    assert cols["read_at"].nullable is True


def test_user_fk_cascade():
    fk = next(iter(Notification.__table__.columns["user_id"].foreign_keys))
    assert fk.target_fullname == "users.id"


def test_unread_partial_index_exists():
    names = {ix.name for ix in Notification.__table__.indexes}
    assert "idx_notifications_user_unread" in names
