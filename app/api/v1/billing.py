# ── Imports ───────────────────────────────────────────────────────────────────
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_db
from app.models.organization import Organization, PlanType
from app.models.user import User
from app.services import stripe_service

router = APIRouter(prefix="/billing", tags=["Billing"])

# ── Schemas ───────────────────────────────────────────────────────────────────


class CheckoutRequest(BaseModel):
    plan: PlanType


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/plans", status_code=status.HTTP_200_OK)
async def list_plans() -> list[dict[str, Any]]:
    """Lists the available subscription plans, price tiers, and feature lists."""
    return [
        {
            "plan": PlanType.FREE.value,
            "name": "Free Plan",
            "price": 0.00,
            "features": [
                "1 User",
                "Basic AI Access",
                "100 Tokens / day",
            ],
        },
        {
            "plan": PlanType.PRO.value,
            "name": "Pro Plan",
            "price": 19.00,
            "features": [
                "Unlimited Users",
                "Premium AI Access",
                "100,000 Tokens / month",
                "2FA Security",
            ],
        },
        {
            "plan": PlanType.ENTERPRISE.value,
            "name": "Enterprise Plan",
            "price": 99.00,
            "features": [
                "Custom SLAs",
                "Dedicated Resources",
                "Unlimited AI Tokens",
                "Advanced Audit Logs",
            ],
        },
    ]


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def create_checkout(
    body: CheckoutRequest,
    user: User = Depends(current_active_user),
) -> dict[str, str]:
    """Generates a Stripe checkout session url to subscribe the user's organization."""
    if not user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any organization",
        )

    try:
        url = await stripe_service.create_checkout_session(
            org_id=user.org_id,
            plan=body.plan,
            email=user.email,
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/portal", status_code=status.HTTP_200_OK)
async def create_portal(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Generates a Stripe billing portal session url to allow card and subscription updates."""
    if not user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any organization",
        )

    stmt = select(Organization).where(Organization.id == user.org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org or not org.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active billing history found for this organization",
        )

    try:
        url = await stripe_service.create_billing_portal_session(
            stripe_customer_id=org.stripe_customer_id
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
