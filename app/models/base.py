from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # সব model এর parent - alembic env.py তে Base.metadata দরকার
    pass


class TimestampMixin:
    """
    created_at আর updated_at সব table এ থাকা উচিত।
    Mixin হিসেবে রাখা হয়েছে কারণ কিছু join table এ id লাগে না কিন্তু timestamp লাগে।
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),  # UPDATE query এ automatically set হবে
        nullable=False,
    )


class BaseModel(TimestampMixin, Base):
    """
    সব primary table এই class extend করবে।
    UUID primary key - integer id এর চেয়ে:
    - enumeration attack থেকে safe
    - distributed system এ collision নেই
    - URL এ expose করা যায়
    """

    __abstract__ = True  # এই class এর নিজস্ব table হবে না

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TenantMixin:
    """
    Multi-tenancy এর core building block।
    এই mixin যে model এ থাকবে, সেই table এ org_id column থাকবে।

    Usage:
        class Product(TenantMixin, BaseModel):
            __tablename__ = "products"
            ...

    Rules:
    - সব tenant-scoped model এ এই mixin use করো
    - TenantService সব query তে org_id filter automatically add করে
    - Direct query করলে org_id filter ভুলে যাওয়ার risk আছে - TenantService use করো
    - organizations table আগে তৈরি হওয়া দরকার (Commit 3 এ হবে)
    """

    org_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # প্রতিটা query তে org_id filter থাকবে - index ছাড়া full scan হবে
    )
