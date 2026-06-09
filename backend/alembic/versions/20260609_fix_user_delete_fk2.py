"""Fix remaining FK constraints blocking user deletion (part 2)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f9a1
Create Date: 2026-06-09

tickets.creator_id  → nullable + ON DELETE SET NULL
phone_otp_audit.user_id → ON DELETE CASCADE  (audit log, safe to purge)
"""

from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f9a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tickets.creator_id: make nullable, add SET NULL on delete
    op.drop_constraint("tickets_creator_id_fkey", "tickets", type_="foreignkey")
    op.alter_column("tickets", "creator_id", nullable=True)
    op.create_foreign_key(
        "tickets_creator_id_fkey",
        "tickets",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # phone_otp_audit.user_id: replace plain FK with CASCADE
    op.drop_constraint(
        "phone_otp_audit_user_id_fkey", "phone_otp_audit", type_="foreignkey"
    )
    op.create_foreign_key(
        "phone_otp_audit_user_id_fkey",
        "phone_otp_audit",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Revert phone_otp_audit
    op.drop_constraint(
        "phone_otp_audit_user_id_fkey", "phone_otp_audit", type_="foreignkey"
    )
    op.create_foreign_key(
        "phone_otp_audit_user_id_fkey",
        "phone_otp_audit",
        "users",
        ["user_id"],
        ["id"],
    )

    # Revert tickets.creator_id
    op.drop_constraint("tickets_creator_id_fkey", "tickets", type_="foreignkey")
    op.alter_column("tickets", "creator_id", nullable=False)
    op.create_foreign_key(
        "tickets_creator_id_fkey",
        "tickets",
        "users",
        ["creator_id"],
        ["id"],
    )
