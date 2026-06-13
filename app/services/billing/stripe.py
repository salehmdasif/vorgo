import stripe
from datetime import datetime, UTC
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, PlanType, SubscriptionStatus
from app.services.billing.base import BaseBillingService

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeBillingService(BaseBillingService):
    """Stripe Implementation of the Unified Billing Service."""

    def _get_price_id_for_plan(self, plan: PlanType) -> str:
        mapping = {
            PlanType.FREE: settings.STRIPE_FREE_PRICE_ID,
            PlanType.PRO: settings.STRIPE_PRO_PRICE_ID,
            PlanType.ENTERPRISE: settings.STRIPE_ENTERPRISE_PRICE_ID,
        }
        price_id = mapping.get(plan)
        if not price_id:
            raise ValueError(f"Stripe Price ID not configured for plan: {plan}")
        return price_id

    async def create_checkout_session(
        self, org_id: UUID, plan: PlanType, email: str
    ) -> str:
        price_id = self._get_price_id_for_plan(plan)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/dashboard/billing?status=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/billing?status=cancel",
            metadata={"org_id": str(org_id), "plan": plan.value},
        )
        return session.url

    async def create_portal_session(self, customer_id: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard/billing",
        )
        return session.url

    async def handle_webhook(
        self, db: AsyncSession, payload: bytes, signature: str
    ) -> None:
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            raise ValueError("Invalid Stripe signature verification") from e
        except ValueError as e:
            raise ValueError("Invalid Stripe webhook payload") from e

        event_type = event.get("type")
        data_object = event.get("data", {}).get("object", {})

        if event_type in [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ]:
            await self._process_subscription_change(db, data_object)

    async def _process_subscription_change(
        self, db: AsyncSession, subscription: dict[str, Any]
    ) -> None:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")

        metadata = subscription.get("metadata", {})
        org_id_str = metadata.get("org_id")
        plan_str = metadata.get("plan")

        if not plan_str:
            items = subscription.get("items", {}).get("data", [])
            if items:
                price_id = items[0].get("price", {}).get("id")
                if price_id == settings.STRIPE_FREE_PRICE_ID:
                    plan_str = PlanType.FREE.value
                elif price_id == settings.STRIPE_PRO_PRICE_ID:
                    plan_str = PlanType.PRO.value
                elif price_id == settings.STRIPE_ENTERPRISE_PRICE_ID:
                    plan_str = PlanType.ENTERPRISE.value

        stripe_status = subscription.get("status")
        status_mapping = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID,
        }
        mapped_status = status_mapping.get(stripe_status, SubscriptionStatus.CANCELED)

        org = None
        if org_id_str:
            try:
                stmt = select(Organization).where(Organization.id == UUID(org_id_str))
                result = await db.execute(stmt)
                org = result.scalar_one_or_none()
            except ValueError:
                pass

        if not org and subscription_id:
            stmt = select(Organization).where(
                Organization.billing_subscription_id == subscription_id
            )
            result = await db.execute(stmt)
            org = result.scalar_one_or_none()

        if not org and customer_id:
            stmt = select(Organization).where(
                Organization.billing_customer_id == customer_id
            )
            result = await db.execute(stmt)
            org = result.scalar_one_or_none()

        if org:
            org.billing_provider = "stripe"
            org.billing_customer_id = customer_id
            org.billing_subscription_id = subscription_id
            org.stripe_customer_id = customer_id
            org.stripe_subscription_id = subscription_id
            org.subscription_status = mapped_status
            if plan_str:
                org.plan = PlanType(plan_str)

            trial_end = subscription.get("trial_end")
            if trial_end:
                org.trial_ends_at = datetime.fromtimestamp(trial_end, UTC)
            else:
                org.trial_ends_at = None

            db.add(org)
            await db.flush()
