"""optimise_indexes

Revision ID: a1b2c3d4e5f6
Revises: 27cae697e8e7
Create Date: 2026-05-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "27cae697e8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_car_images_car_id ON car_images (car_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_created_at_desc ON cars (created_at DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_status_created_at ON cars (status, created_at DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_deals_car_id ON deals (car_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_deals_client_id ON deals (client_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_deals_manager_id ON deals (manager_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_deals_deal_date ON deals (deal_date)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_viewings_car_id ON viewings (car_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_viewings_client_id ON viewings (client_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_viewings_car_date_result "
        "ON viewings (car_id, viewing_date, result)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_viewings_car_date_result"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_viewings_client_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_viewings_car_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_deals_deal_date"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_deals_manager_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_deals_client_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_deals_car_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_status_created_at"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_created_at_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_car_images_car_id"))
