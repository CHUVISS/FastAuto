"""add_thumb_url_to_car_images

Revision ID: 935201a5d9f9
Revises: 85d6782fda00
Create Date: 2026-03-22 01:33:24.092488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '935201a5d9f9'
down_revision: Union[str, Sequence[str], None] = '85d6782fda00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "car_images",
        sa.Column("thumb_url", sa.String(length=500), nullable=True),
    )
    op.execute(
        "UPDATE car_images SET thumb_url = replace(url, '.jpg', '_thumb.jpg')"
    )
    op.alter_column("car_images", "thumb_url", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("car_images", "thumb_url")
