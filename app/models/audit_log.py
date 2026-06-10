from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantMixin


class AuditLog(TenantMixin, BaseModel):
    """
    Immutable audit trail. Write-only - never update or delete rows.

    Write on: login, logout, password change, member invite/remove,
    subscription change, API key create/revoke, admin impersonation, data export.
    """

    __tablename__ = "audit_logs"

    # nullable — system-triggered actions (e.g. scheduled job) have no user
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # machine-readable action: "user.login", "member.invite", "subscription.canceled"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    extra: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
