"""create feature flags

Revision ID: b7b51b7593c6
Revises: a3a8b417e4cf
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7b51b7593c6"
down_revision: Union[str, None] = "a3a8b417e4cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("enabled_globally", sa.Boolean(), nullable=False),
        sa.Column("enabled_for_plans", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("enabled_for_orgs", postgresql.ARRAY(sa.UUID()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feature_flags_name"), "feature_flags", ["name"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_flags_name"), table_name="feature_flags")
    op.drop_table("feature_flags")
