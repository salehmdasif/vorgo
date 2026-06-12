"""create core models

Revision ID: a3a8b417e4cf
Revises: 
Create Date: 2026-06-10 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a3a8b417e4cf"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Upgrade Migration ─────────────────────────────────────────────────────────


def upgrade() -> None:
    # ── Create Enums ──────────────────────────────────────────────────────────
    plan_type = postgresql.ENUM("free", "pro", "enterprise", name="plan_type")
    plan_type.create(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM(
        "trialing", "active", "past_due", "canceled", "unpaid", name="subscription_status"
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    user_role = postgresql.ENUM("super_admin", "admin", "user", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)

    # ── Create Tables ─────────────────────────────────────────────────────────
    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "plan",
            postgresql.ENUM("free", "pro", "enterprise", name="plan_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "subscription_status",
            postgresql.ENUM(
                "trialing",
                "active",
                "past_due",
                "canceled",
                "unpaid",
                name="subscription_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index(
        op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True
    )

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM("super_admin", "admin", "user", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("totp_secret", sa.String(length=255), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False),
        sa.Column("backup_codes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"], unique=False)

    # 3. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_org_id"), "audit_logs", ["org_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False
    )


# ── Downgrade Migration ───────────────────────────────────────────────────────


def downgrade() -> None:
    # ── Drop Tables ───────────────────────────────────────────────────────────
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_org_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")

    # ── Drop Enums ────────────────────────────────────────────────────────────
    user_role = postgresql.ENUM("super_admin", "admin", "user", name="user_role")
    user_role.drop(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM(
        "trialing", "active", "past_due", "canceled", "unpaid", name="subscription_status"
    )
    subscription_status.drop(op.get_bind(), checkfirst=True)

    plan_type = postgresql.ENUM("free", "pro", "enterprise", name="plan_type")
    plan_type.drop(op.get_bind(), checkfirst=True)
