"""reservation domain: reservations + favorites tables, listing columns, booking fk

Revision ID: a1b2c3d4e5f7
Revises: b9c1d2e3a407
Create Date: 2026-05-27

Additive migration for the deposit-reservation redesign. Adds the
``reservations`` and ``favorites`` tables, the listing ``sale_address`` /
``accepts_cash`` / ``accepts_transfer`` columns, and ``viewing_bookings``
``reservation_id``. Idempotent; no CONCURRENTLY (Alembic txn wrapper).
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "b9c1d2e3a407"
branch_labels = None
depends_on = None

# Native PG enums, names matching SQLModel's auto-generated types so that
# the migration-built schema equals the model (autogenerate diff stays empty).
# ``create_type=False`` (honored by postgresql.ENUM) keeps create_table from
# emitting CREATE TYPE — the guarded DO-block in ``upgrade`` owns the lifecycle.
reservation_status = postgresql.ENUM(
    "pending_payment",
    "active",
    "settling",
    "completed",
    "cancelled",
    name="reservationstatus",
    create_type=False,
)
reservation_outcome = postgresql.ENUM(
    "sold", "not_sold", name="reservationoutcome", create_type=False
)
outcome_party = postgresql.ENUM(
    "buyer", "seller", name="outcomeparty", create_type=False
)
cancel_reason = postgresql.ENUM(
    "buyer_cancelled",
    "seller_declined",
    "payment_abandoned",
    "hold_expired",
    "hold_released_externally",
    "admin",
    name="cancelreason",
    create_type=False,
)
_ENUM_DEFS = {
    "reservationstatus": reservation_status.enums,
    "reservationoutcome": reservation_outcome.enums,
    "outcomeparty": outcome_party.enums,
    "cancelreason": cancel_reason.enums,
}


def _create_enum(name: str, values: list[str]) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT FROM pg_type WHERE typname = '{name}') THEN "
        f"CREATE TYPE {name} AS ENUM ({labels}); "
        f"END IF; END $$;"
    )


def upgrade() -> None:
    for name, values in _ENUM_DEFS.items():
        _create_enum(name, values)

    op.create_table(
        "reservations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("buyer_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("deposit_amount", sa.BigInteger(), nullable=False),
        sa.Column("yk_payment_id", sa.String(length=50), nullable=True),
        sa.Column("status", reservation_status, nullable=False),
        sa.Column("outcome", reservation_outcome, nullable=True),
        sa.Column("outcome_set_by", outcome_party, nullable=True),
        sa.Column("outcome_set_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "buyer_change_used",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "seller_change_used",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deposit_released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", cancel_reason, nullable=True),
        sa.Column("payment_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hold_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correction_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_prompt_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservations_listing_id", "reservations", ["listing_id"])
    op.create_index("ix_reservations_buyer_id", "reservations", ["buyer_id"])
    op.create_index("ix_reservations_seller_id", "reservations", ["seller_id"])
    op.create_index("ix_reservations_status", "reservations", ["status"])
    op.create_index(
        "uniq_active_reservation_per_listing",
        "reservations",
        ["listing_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('completed','cancelled')"),
    )
    op.create_index(
        "idx_reservation_hold_deadline",
        "reservations",
        ["hold_deadline"],
        postgresql_where=sa.text("status IN ('pending_payment','active')"),
    )
    op.create_index(
        "idx_reservation_correction_deadline",
        "reservations",
        ["correction_deadline"],
        postgresql_where=sa.text("status = 'settling'"),
    )
    op.create_index(
        "idx_reservation_prompt_scan",
        "reservations",
        ["last_prompt_at"],
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index(
        "uniq_favorite_user_listing",
        "favorites",
        ["user_id", "listing_id"],
        unique=True,
    )
    op.create_index("idx_favorite_listing", "favorites", ["listing_id"])

    op.add_column(
        "listings", sa.Column("sale_address", sa.String(length=300), nullable=True)
    )
    op.add_column(
        "listings",
        sa.Column(
            "accepts_cash",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "accepts_transfer",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.add_column(
        "viewing_bookings", sa.Column("reservation_id", sa.Uuid(), nullable=True)
    )
    op.create_index(
        "ix_viewing_bookings_reservation_id",
        "viewing_bookings",
        ["reservation_id"],
    )
    op.create_foreign_key(
        "fk_viewing_bookings_reservation",
        "viewing_bookings",
        "reservations",
        ["reservation_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_viewing_bookings_reservation", "viewing_bookings", type_="foreignkey"
    )
    op.drop_index("ix_viewing_bookings_reservation_id", table_name="viewing_bookings")
    op.drop_column("viewing_bookings", "reservation_id")

    op.drop_column("listings", "accepts_transfer")
    op.drop_column("listings", "accepts_cash")
    op.drop_column("listings", "sale_address")

    op.drop_index("idx_favorite_listing", table_name="favorites")
    op.drop_index("uniq_favorite_user_listing", table_name="favorites")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")

    op.drop_index("idx_reservation_prompt_scan", table_name="reservations")
    op.drop_index("idx_reservation_correction_deadline", table_name="reservations")
    op.drop_index("idx_reservation_hold_deadline", table_name="reservations")
    op.drop_index("uniq_active_reservation_per_listing", table_name="reservations")
    op.drop_index("ix_reservations_status", table_name="reservations")
    op.drop_index("ix_reservations_seller_id", table_name="reservations")
    op.drop_index("ix_reservations_buyer_id", table_name="reservations")
    op.drop_index("ix_reservations_listing_id", table_name="reservations")
    op.drop_table("reservations")

    for name in _ENUM_DEFS:
        op.execute(f"DROP TYPE IF EXISTS {name}")
