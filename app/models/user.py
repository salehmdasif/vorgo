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
    fastapi-users compatible User model।

    SQLAlchemyBaseUserTableUUID থেকে পাওয়া fields:
        id (UUID, primary key)
        email (str, unique)
        hashed_password (str)
        is_active (bool)
        is_verified (bool)
        is_superuser (bool)  - super_admin এর জন্য True

    আমাদের extra fields নিচে।

    Note: BaseModel extend করা যাবে না - id conflict হবে।
    TimestampMixin + Base আলাদা করে extend করা হচ্ছে।
    """

    __tablename__ = "users"

    # org_id nullable - super_admin এর কোনো org নেই
    # normal user এর জন্য always set থাকবে
    # Organization delete হলে SET NULL - user account maintain থাকবে
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

    # ── 2FA ───────────────────────────────────────────────────────────────────
    # totp_secret - AES-256 encrypted করে store করো (app/core/security/two_factor.py)
    # plaintext store করা risky - DB leak হলে সব user এর 2FA compromise হবে
    totp_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # backup_codes - 8টা, bcrypt hashed, one-time use
    # use হলে সেই code array থেকে delete করো
    backup_codes: Mapped[list] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )
