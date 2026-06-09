"""Add user_preferences table for AI recommendation weight engine

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tag_type", sa.String(length=50), nullable=False),
        sa.Column("tag_value", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "tag_type", "tag_value", name="uq_user_pref"),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index("ix_user_preferences_tag_type", "user_preferences", ["tag_type"])
    op.create_index("ix_user_preferences_tag_value", "user_preferences", ["tag_value"])


def downgrade() -> None:
    op.drop_index("ix_user_preferences_tag_value", table_name="user_preferences")
    op.drop_index("ix_user_preferences_tag_type", table_name="user_preferences")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
