"""Cascade delete all user data on user deletion

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-09

Adds proper ON DELETE rules so deleting a user automatically removes
all their listings, reservations, viewing bookings, and related data.

Chain:
  user deleted
    → listings CASCADE  (seller_id)
        → listing_images CASCADE       (already was CASCADE)
        → viewing_windows CASCADE      (already was CASCADE)
        → favorites CASCADE            (already was CASCADE)
        → reservations CASCADE         (listing_id — was plain FK)
            → viewing_bookings SET NULL (reservation_id — nullable)
            → tickets SET NULL          (reservation_id — nullable)
        → viewing_bookings CASCADE     (listing_id — was plain FK)
        → tickets SET NULL             (listing_id — nullable)
    → reservations CASCADE  (buyer_id / seller_id — were plain FKs)
    → viewing_bookings CASCADE  (buyer_id — was plain FK)
"""

from sqlalchemy.engine import Inspector

from alembic import op


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def _drop_fk(table: str, constraint_name: str) -> None:
    """Drop FK by explicit name; no-op if it doesn't exist."""
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    existing = {fk["name"] for fk in insp.get_foreign_keys(table)}
    if constraint_name in existing:
        op.drop_constraint(constraint_name, table, type_="foreignkey")


def _drop_fk_by_column(table: str, column: str) -> str | None:
    """Drop FK by column name; returns the constraint name that was dropped."""
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    for fk in insp.get_foreign_keys(table):
        if fk["constrained_columns"] == [column] and fk.get("name"):
            op.drop_constraint(fk["name"], table, type_="foreignkey")
            return fk["name"]
    return None


def upgrade() -> None:
    # ── listings.seller_id → CASCADE ─────────────────────────────────────────
    _drop_fk_by_column("listings", "seller_id")
    op.create_foreign_key(
        "listings_seller_id_fkey", "listings", "users",
        ["seller_id"], ["id"], ondelete="CASCADE",
    )

    # ── reservations.listing_id → CASCADE ────────────────────────────────────
    _drop_fk_by_column("reservations", "listing_id")
    op.create_foreign_key(
        "reservations_listing_id_fkey", "reservations", "listings",
        ["listing_id"], ["id"], ondelete="CASCADE",
    )

    # ── reservations.buyer_id → CASCADE ──────────────────────────────────────
    _drop_fk_by_column("reservations", "buyer_id")
    op.create_foreign_key(
        "reservations_buyer_id_fkey", "reservations", "users",
        ["buyer_id"], ["id"], ondelete="CASCADE",
    )

    # ── reservations.seller_id → CASCADE ─────────────────────────────────────
    _drop_fk_by_column("reservations", "seller_id")
    op.create_foreign_key(
        "reservations_seller_id_fkey", "reservations", "users",
        ["seller_id"], ["id"], ondelete="CASCADE",
    )

    # ── viewing_bookings.listing_id → CASCADE ─────────────────────────────────
    _drop_fk_by_column("viewing_bookings", "listing_id")
    op.create_foreign_key(
        "viewing_bookings_listing_id_fkey", "viewing_bookings", "listings",
        ["listing_id"], ["id"], ondelete="CASCADE",
    )

    # ── viewing_bookings.buyer_id → CASCADE ───────────────────────────────────
    _drop_fk_by_column("viewing_bookings", "buyer_id")
    op.create_foreign_key(
        "viewing_bookings_buyer_id_fkey", "viewing_bookings", "users",
        ["buyer_id"], ["id"], ondelete="CASCADE",
    )

    # ── viewing_bookings.reservation_id → SET NULL ────────────────────────────
    dropped = _drop_fk_by_column("viewing_bookings", "reservation_id")
    if dropped is not None:
        op.create_foreign_key(
            "viewing_bookings_reservation_id_fkey", "viewing_bookings", "reservations",
            ["reservation_id"], ["id"], ondelete="SET NULL",
        )

    # ── tickets.listing_id → SET NULL ─────────────────────────────────────────
    _drop_fk_by_column("tickets", "listing_id")
    op.create_foreign_key(
        "tickets_listing_id_fkey", "tickets", "listings",
        ["listing_id"], ["id"], ondelete="SET NULL",
    )

    # ── tickets.reservation_id → SET NULL ─────────────────────────────────────
    # Was named "fk_tickets_reservation" in migration b2c3d4e5f8a1
    _drop_fk("tickets", "fk_tickets_reservation")
    _drop_fk_by_column("tickets", "reservation_id")  # fallback
    op.create_foreign_key(
        "fk_tickets_reservation", "tickets", "reservations",
        ["reservation_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    # Revert in reverse order

    _drop_fk("tickets", "fk_tickets_reservation")
    op.create_foreign_key(
        "fk_tickets_reservation", "tickets", "reservations",
        ["reservation_id"], ["id"],
    )

    _drop_fk("tickets", "tickets_listing_id_fkey")
    op.create_foreign_key(
        "tickets_listing_id_fkey", "tickets", "listings",
        ["listing_id"], ["id"],
    )

    _drop_fk("viewing_bookings", "viewing_bookings_reservation_id_fkey")
    op.create_foreign_key(
        "viewing_bookings_reservation_id_fkey", "viewing_bookings", "reservations",
        ["reservation_id"], ["id"],
    )

    _drop_fk("viewing_bookings", "viewing_bookings_buyer_id_fkey")
    op.create_foreign_key(
        "viewing_bookings_buyer_id_fkey", "viewing_bookings", "users",
        ["buyer_id"], ["id"],
    )

    _drop_fk("viewing_bookings", "viewing_bookings_listing_id_fkey")
    op.create_foreign_key(
        "viewing_bookings_listing_id_fkey", "viewing_bookings", "listings",
        ["listing_id"], ["id"],
    )

    _drop_fk("reservations", "reservations_seller_id_fkey")
    op.create_foreign_key(
        "reservations_seller_id_fkey", "reservations", "users",
        ["seller_id"], ["id"],
    )

    _drop_fk("reservations", "reservations_buyer_id_fkey")
    op.create_foreign_key(
        "reservations_buyer_id_fkey", "reservations", "users",
        ["buyer_id"], ["id"],
    )

    _drop_fk("reservations", "reservations_listing_id_fkey")
    op.create_foreign_key(
        "reservations_listing_id_fkey", "reservations", "listings",
        ["listing_id"], ["id"],
    )

    _drop_fk("listings", "listings_seller_id_fkey")
    op.create_foreign_key(
        "listings_seller_id_fkey", "listings", "users",
        ["seller_id"], ["id"],
    )
