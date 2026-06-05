from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    # সব model এর parent — alembic env.py তে Base.metadata দরকার
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
    UUID primary key — integer id এর চেয়ে:
    - enumeration attack থেকে safe
    - distributed system এ collision নেই
    - URL এ expose করা যায়
    """

    __abstract__ = True  # এই class এর নিজস্ব table হবে না

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
