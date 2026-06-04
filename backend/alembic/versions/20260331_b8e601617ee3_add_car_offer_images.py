"""add_car_offer_images

Revision ID: b8e601617ee3
Revises: 7a6d389f1733
Create Date: 2026-03-31 00:22:22.928040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e601617ee3'
down_revision: Union[str, Sequence[str], None] = '7a6d389f1733'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "car_offer_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("thumb_url", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"], ["car_offers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_car_offer_images_offer_id",
        "car_offer_images",
        ["offer_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_car_offer_images_offer_id", table_name="car_offer_images")
    op.drop_table("car_offer_images")
