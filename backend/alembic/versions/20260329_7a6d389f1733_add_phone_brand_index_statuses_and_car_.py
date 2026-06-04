"""add_phone_brand_index_statuses_and_car_offers

Revision ID: 7a6d389f1733
Revises: 935201a5d9f9
Create Date: 2026-03-29 02:30:33.954472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import ENUM as PgENUM

# revision identifiers, used by Alembic.
revision: str = '7a6d389f1733'
down_revision: Union[str, Sequence[str], None] = '935201a5d9f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FUELTYPE = PgENUM(name="fueltype", create_type=False)
TRANSMISSION = PgENUM(name="transmission", create_type=False)
BODYTYPE = PgENUM(name="bodytype", create_type=False)


def upgrade() -> None:
    op.drop_index("ix_cars_make", table_name="cars")
    op.alter_column("cars", "make", new_column_name="brand")
    op.create_index("ix_cars_brand", "cars", ["brand"], unique=False)

    op.add_column(
        "users",
        sa.Column("phone", sa.String(length=20), nullable=True),
    )
    op.create_index(
        "ix_users_phone",
        "users",
        ["phone"],
        unique=True,
        postgresql_where=sa.text("phone IS NOT NULL"),
    )

    op.create_index("ix_clients_phone", "clients", ["phone"], unique=True)
    op.create_index("ix_clients_email", "clients", ["email"], unique=False)

    op.execute("ALTER TYPE viewingresult ADD VALUE IF NOT EXISTS 'confirmed'")
    op.execute("ALTER TYPE viewingresult ADD VALUE IF NOT EXISTS 'cancelled_user'")
    op.execute("ALTER TYPE viewingresult ADD VALUE IF NOT EXISTS 'cancelled_manager'")

    op.add_column(
        "viewings",
        sa.Column("viewing_time", sa.Time(), nullable=True),
    )

    op.create_table(
        "car_offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=True),
        sa.Column("car_id", sa.Uuid(), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("mileage", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fuel_type", FUELTYPE, nullable=True),
        sa.Column("transmission", TRANSMISSION, nullable=True),
        sa.Column("body_type", BODYTYPE, nullable=True),
        sa.Column("engine_volume", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("engine_power", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="carofferstatustype"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("rejection_reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["car_id"], ["cars.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_car_offers_user_id", "car_offers", ["user_id"])
    op.create_index("ix_car_offers_status", "car_offers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_car_offers_status", table_name="car_offers")
    op.drop_index("ix_car_offers_user_id", table_name="car_offers")
    op.drop_table("car_offers")
    op.execute("DROP TYPE IF EXISTS carofferstatustype")

    op.drop_column("viewings", "viewing_time")

    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_index("ix_clients_phone", table_name="clients")

    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "phone")

    op.drop_index("ix_cars_brand", table_name="cars")
    op.alter_column("cars", "brand", new_column_name="make")
    op.create_index("ix_cars_make", "cars", ["make"], unique=False)
