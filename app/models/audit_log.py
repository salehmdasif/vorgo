from uuid import UUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantMixin


class AuditLog(TenantMixin, BaseModel):
    """
    Immutable audit trail — sensitive action এর record।

    Write-only: কখনো update বা delete করা হবে না।
    BaseModel থেকে updated_at আসবে কিন্তু সেটা কখনো change হবে না।

    কখন লিখতে হবে:
        - login, logout, password change
        - member invite, role change, member remove
        - subscription change
        - API key create/revoke
        - admin impersonation
        - data export
    """

    __tablename__ = "audit_logs"

    # user_id nullable — system-triggered action এ user নাও থাকতে পারে
    # (e.g., scheduled job এ subscription expire করা)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # action — machine-readable: "user.login", "member.invite", "subscription.canceled"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # resource_type + resource_id — কোন object এ action হয়েছে
    # e.g., resource_type="user", resource_id="uuid-of-the-user"
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max 45 chars
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # extra data — before/after values, reason, etc.
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
