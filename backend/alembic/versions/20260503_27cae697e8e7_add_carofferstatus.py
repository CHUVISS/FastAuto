"""add carofferstatus

Revision ID: 27cae697e8e7
Revises: c7e0eb59076f
Create Date: 2026-05-03 00:49:54.318929

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '27cae697e8e7'
down_revision: Union[str, Sequence[str], None] = 'c7e0eb59076f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

car_offer_status = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="carofferstatus",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    car_offer_status.create(bind, checkfirst=True)

    op.execute("ALTER TABLE car_offers ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE car_offers
        ALTER COLUMN status TYPE carofferstatus
        USING status::text::carofferstatus
    """)
    op.execute("""
        ALTER TABLE car_offers
        ALTER COLUMN status SET DEFAULT 'pending'::carofferstatus
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE car_offers ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE car_offers
        ALTER COLUMN status TYPE varchar
        USING status::text
    """)
    op.execute("ALTER TABLE car_offers ALTER COLUMN status SET DEFAULT 'pending'")

    car_offer_status.drop(op.get_bind(), checkfirst=True)
