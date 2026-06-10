import enum
from uuid import UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class User(SQLAlchemyBaseUserTableUUID, TimestampMixin, Base):
    """
    fastapi-users compatible User model.

    Inherited from SQLAlchemyBaseUserTableUUID:
        id, email, hashed_password, is_active, is_verified, is_superuser

    Do not extend BaseModel - id conflict.
    TimestampMixin and Base are extended separately.
    """

    __tablename__ = "users"

    # nullable - super_admin has no org, regular users always have one
    # SET NULL on org delete to preserve user accounts
    org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=True),
        default=UserRole.USER,
        nullable=False,
    )

    # totp_secret must be AES-256 encrypted before storing (app/core/security/two_factor.py)
    totp_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 8 bcrypt-hashed one-time backup codes - delete each after use
    backup_codes: Mapped[list] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )
