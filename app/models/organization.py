import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # slug - subdomain routing এ use হয়: company.yoursaas.com
    # unique + index: প্রতিটা request এ subdomain lookup হবে, fast হওয়া দরকার
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    plan: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType, name="plan_type", create_type=True),
        default=PlanType.FREE,
        nullable=False,
    )

    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", create_type=True),
        default=SubscriptionStatus.TRIALING,
        nullable=False,
    )

    # trial_ends_at - None মানে trial নেই (active subscription বা free plan)
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Stripe IDs - billing এ দরকার, None মানে এখনো Stripe এ register হয়নি
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,  # একটা org এর একটাই Stripe customer থাকবে
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    # per-org settings: timezone, locale, branding, feature toggles
    # JSONB - structure fix না করেই যেকোনো config store করা যায়
    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
