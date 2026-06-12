"""create invitations

Revision ID: 9e3a6f1d2c3b
Revises: b7b51b7593c6
Create Date: 2026-06-11 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9e3a6f1d2c3b"
down_revision: Union[str, None] = "b7b51b7593c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("super_admin", "admin", "user", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("invited_by", sa.UUID(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_invitations_token"), "invitations", ["token"], unique=True
    )
    op.create_index(
        op.f("ix_invitations_email"), "invitations", ["email"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_invitations_email"), table_name="invitations")
    op.drop_index(op.f("ix_invitations_token"), table_name="invitations")
    op.drop_table("invitations")
