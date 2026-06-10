# ── Imports ───────────────────────────────────────────────────────────────────
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# ── Model Definition ──────────────────────────────────────────────────────────


class FeatureFlag(BaseModel):
    """
    Model representing feature flags.
    Controls access to specific SaaS application features dynamically.
    """

    __tablename__ = "feature_flags"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    enabled_globally: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # List of plans where this feature is enabled: ["free", "pro", "enterprise"]
    enabled_for_plans: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )

    # List of organization UUIDs that have custom access to this feature
    enabled_for_orgs: Mapped[list[UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        default=list,
        nullable=False,
    )
