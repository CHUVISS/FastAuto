"""marketplace tables

Revision ID: e5af69fdead9
Revises: 82cf852f0775
Create Date: 2026-05-23 23:27:53.280963

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "e5af69fdead9"
down_revision: Union[str, Sequence[str], None] = "82cf852f0775"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payout_method_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("payout_method_id", sa.Uuid(), nullable=True),
        sa.Column("event", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column(
            "old_card_last4",
            sqlmodel.sql.sqltypes.AutoString(length=4),
            nullable=True,
        ),
        sa.Column(
            "new_card_last4",
            sqlmodel.sql.sqltypes.AutoString(length=4),
            nullable=True,
        ),
        sa.Column("ip", sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
        sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_payout_audit_user",
        "payout_method_audit",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "payout_methods",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("payout_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "card_last4", sqlmodel.sql.sqltypes.AutoString(length=4), nullable=True
        ),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column(
            "recipient_full_name",
            sqlmodel.sql.sqltypes.AutoString(length=200),
            nullable=False,
        ),
        sa.Column(
            "is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_payout_methods_user", "payout_methods", ["user_id"], unique=False
    )
    op.create_index(
        "uniq_default_payout_method",
        "payout_methods",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )
    op.create_table(
        "phone_otp_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("phone", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column(
            "purpose", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "verified", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_otp_audit_phone_sent", "phone_otp_audit", ["phone", "sent_at"], unique=False
    )
    op.create_index(
        "idx_otp_audit_user_sent",
        "phone_otp_audit",
        ["user_id", "sent_at"],
        unique=False,
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column(
            "modification_id",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
        ),
        sa.Column("mark_id", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column(
            "model_id", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column(
            "body_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column(
            "engine_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=False),
        sa.Column("color", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("vin", sqlmodel.sql.sqltypes.AutoString(length=17), nullable=True),
        sa.Column(
            "license_plate", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=True
        ),
        sa.Column("license_plate_edit_count", sa.Integer(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "condition",
            sa.Enum("excellent", "good", "fair", "poor", name="condition"),
            nullable=False,
        ),
        sa.Column(
            "city_of_sale", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_review",
                "active",
                "reserved",
                "sold",
                "archived",
                name="listingstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "viewing_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "viewing_repeat_weekly",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("payout_method_id", sa.Uuid(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["payout_method_id"], ["payout_methods.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_active_mark_price",
        "listings",
        ["mark_id", "price", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_active_mark_recency",
        "listings",
        ["mark_id", "created_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_active_model_price",
        "listings",
        ["model_id", "price", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_active_model_recency",
        "listings",
        ["model_id", "created_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_active_price",
        "listings",
        ["price", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_active_recency",
        "listings",
        ["created_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_listings_expiry_active",
        "listings",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("idx_listings_seller", "listings", ["seller_id"], unique=False)
    op.create_index(
        "uniq_active_vin",
        "listings",
        ["vin"],
        unique=True,
        postgresql_where=sa.text("vin IS NOT NULL"),
    )
    op.create_table(
        "listing_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("thumbnail_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_listing_images_listing_id"),
        "listing_images",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "uniq_primary_image",
        "listing_images",
        ["listing_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("buyer_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("payout_method_id", sa.Uuid(), nullable=False),
        sa.Column("yk_deal_id", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column(
            "payment_id", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column(
            "payout_id", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column(
            "refund_id", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True
        ),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column("commission_amount", sa.BigInteger(), nullable=False),
        sa.Column("seller_payout_amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "reserved",
                "viewing_scheduled",
                "viewing_completed",
                "awaiting_payment",
                "paid",
                "completed",
                "payout_failed",
                "cancelled",
                "disputed",
                name="transactionstatus",
            ),
            nullable=False,
        ),
        sa.Column("confirmation_deadline", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["payout_method_id"], ["payout_methods.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tx_deadline_active",
        "transactions",
        ["confirmation_deadline"],
        unique=False,
        postgresql_where=sa.text(
            "status IN ('reserved','viewing_scheduled',"
            "'viewing_completed','awaiting_payment')"
        ),
    )
    op.create_index(
        "idx_tx_payout_intent",
        "transactions",
        ["updated_at"],
        unique=False,
        postgresql_where=sa.text("status = 'paid' AND payout_id IS NULL"),
    )
    op.create_index(
        op.f("ix_transactions_buyer_id"), "transactions", ["buyer_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_listing_id"), "transactions", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_seller_id"), "transactions", ["seller_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_status"), "transactions", ["status"], unique=False
    )
    op.create_index(
        "uniq_active_tx_per_listing",
        "transactions",
        ["listing_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('completed','cancelled')"),
    )
    op.create_table(
        "viewing_windows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("window_date", sa.Date(), nullable=False),
        sa.Column("time_from", sa.Time(), nullable=False),
        sa.Column("time_to", sa.Time(), nullable=False),
        sa.Column(
            "is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_viewing_windows_listing_date",
        "viewing_windows",
        ["listing_id", "window_date"],
        unique=False,
    )
    op.create_index(
        "uniq_window_slot",
        "viewing_windows",
        ["listing_id", "window_date", "time_from", "time_to"],
        unique=True,
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "purchase_dispute",
                "listing_report",
                "moderation_appeal",
                "support_inquiry",
                name="tickettype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "resolved", "closed", name="ticketstatus"),
            nullable=False,
        ),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("listing_id", sa.Uuid(), nullable=True),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
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
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tickets_assignee_id"), "tickets", ["assignee_id"], unique=False
    )
    op.create_index(
        op.f("ix_tickets_creator_id"), "tickets", ["creator_id"], unique=False
    )
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"], unique=False)
    op.create_table(
        "viewing_bookings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("buyer_id", sa.Uuid(), nullable=False),
        sa.Column("window_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("scheduled", "completed", "cancelled", name="bookingstatus"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["window_id"], ["viewing_windows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uniq_active_booking",
        "viewing_bookings",
        ["listing_id", "window_id"],
        unique=True,
        postgresql_where=sa.text("status != 'cancelled'"),
    )
    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("body", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ticket_messages_ticket_id"),
        "ticket_messages",
        ["ticket_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ticket_messages_ticket_id"), table_name="ticket_messages")
    op.drop_table("ticket_messages")
    op.drop_index(
        "uniq_active_booking",
        table_name="viewing_bookings",
        postgresql_where=sa.text("status != 'cancelled'"),
    )
    op.drop_table("viewing_bookings")
    op.drop_index(op.f("ix_tickets_status"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_creator_id"), table_name="tickets")
    op.drop_index(op.f("ix_tickets_assignee_id"), table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("uniq_window_slot", table_name="viewing_windows")
    op.drop_index("idx_viewing_windows_listing_date", table_name="viewing_windows")
    op.drop_table("viewing_windows")
    op.drop_index(
        "uniq_active_tx_per_listing",
        table_name="transactions",
        postgresql_where=sa.text("status NOT IN ('completed','cancelled')"),
    )
    op.drop_index(op.f("ix_transactions_status"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_seller_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_listing_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_buyer_id"), table_name="transactions")
    op.drop_index(
        "idx_tx_payout_intent",
        table_name="transactions",
        postgresql_where=sa.text("status = 'paid' AND payout_id IS NULL"),
    )
    op.drop_index(
        "idx_tx_deadline_active",
        table_name="transactions",
        postgresql_where=sa.text(
            "status IN ('reserved','viewing_scheduled',"
            "'viewing_completed','awaiting_payment')"
        ),
    )
    op.drop_table("transactions")
    op.drop_index(
        "uniq_primary_image",
        table_name="listing_images",
        postgresql_where=sa.text("is_primary = true"),
    )
    op.drop_index(op.f("ix_listing_images_listing_id"), table_name="listing_images")
    op.drop_table("listing_images")
    op.drop_index(
        "uniq_active_vin",
        table_name="listings",
        postgresql_where=sa.text("vin IS NOT NULL"),
    )
    op.drop_index("idx_listings_seller", table_name="listings")
    op.drop_index(
        "idx_listings_expiry_active",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_recency",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_price",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_model_recency",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_model_price",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_mark_recency",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index(
        "idx_active_mark_price",
        table_name="listings",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_table("listings")
    op.drop_index("idx_otp_audit_user_sent", table_name="phone_otp_audit")
    op.drop_index("idx_otp_audit_phone_sent", table_name="phone_otp_audit")
    op.drop_table("phone_otp_audit")
    op.drop_index(
        "uniq_default_payout_method",
        table_name="payout_methods",
        postgresql_where=sa.text("is_default = true"),
    )
    op.drop_index("idx_payout_methods_user", table_name="payout_methods")
    op.drop_table("payout_methods")
    op.drop_index("idx_payout_audit_user", table_name="payout_method_audit")
    op.drop_table("payout_method_audit")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
    op.execute("DROP TYPE IF EXISTS tickettype")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS listingstatus")
    op.execute("DROP TYPE IF EXISTS condition")
