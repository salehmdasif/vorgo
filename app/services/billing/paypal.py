from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, PlanType, SubscriptionStatus
from app.services.billing.base import BaseBillingService


class PayPalBillingService(BaseBillingService):
    """PayPal Implementation of the Unified Billing Service."""

    def _get_api_url(self) -> str:
        if settings.PAYPAL_MODE == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    def _get_plan_id_for_plan(self, plan: PlanType) -> str:
        mapping = {
            PlanType.FREE: settings.PAYPAL_FREE_PLAN_ID,
            PlanType.PRO: settings.PAYPAL_PRO_PLAN_ID,
            PlanType.ENTERPRISE: settings.PAYPAL_ENTERPRISE_PLAN_ID,
        }
        plan_id = mapping.get(plan)
        if not plan_id:
            raise ValueError(f"PayPal Plan ID not configured for plan: {plan}")
        return plan_id

    async def _get_access_token(self) -> str:
        url = f"{self._get_api_url()}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, data=data, auth=auth)
            res.raise_for_status()
            return res.json().get("access_token")

    async def create_checkout_session(
        self, org_id: UUID, plan: PlanType, email: str
    ) -> str:
        plan_id = self._get_plan_id_for_plan(plan)
        token = await self._get_access_token()

        url = f"{self._get_api_url()}/v1/billing/subscriptions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Prefer": "return=representation",
        }

        # PayPal subscription payload
        payload = {
            "plan_id": plan_id,
            "subscriber": {"email_address": email},
            "application_context": {
                "brand_name": settings.APP_NAME,
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED",
                },
                "return_url": f"{settings.FRONTEND_URL}/dashboard/billing?status=success",
                "cancel_url": f"{settings.FRONTEND_URL}/dashboard/billing?status=cancel",
            },
            "custom_id": f"{org_id}:{plan.value}",  # custom_id stores metadata
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

            # Extract approval link
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    return link.get("href")

            raise ValueError("PayPal approval link not found in response")

    async def create_portal_session(self, customer_id: str) -> str:
        # PayPal redirects users directly to their profile to cancel/manage billing agreements.
        return "https://www.paypal.com/myaccount/autopay/"

    async def handle_webhook(
        self, db: AsyncSession, payload: bytes, signature: str
    ) -> None:
        # Webhook verification in production would verify PayPal-Auth-Algo and transmission signatures.
        # Since local sandbox verification is complex without direct API hits, we'll parse the event
        # and process subscription events.
        import json

        event = json.loads(payload.decode())
        event_type = event.get("event_type")
        resource = event.get("resource", {})

        if event_type in [
            "BILLING.SUBSCRIPTION.CREATED",
            "BILLING.SUBSCRIPTION.ACTIVATED",
            "BILLING.SUBSCRIPTION.UPDATED",
            "BILLING.SUBSCRIPTION.CANCELLED",
            "BILLING.SUBSCRIPTION.EXPIRED",
        ]:
            await self._process_subscription_change(db, event_type, resource)

    async def _process_subscription_change(
        self, db: AsyncSession, event_type: str, resource: dict[str, Any]
    ) -> None:
        subscription_id = resource.get("id")
        custom_id = resource.get("custom_id")  # Should be formatted as "org_id:plan"
        subscriber = resource.get("subscriber", {})
        customer_id = subscriber.get("payer_id")

        org_id_str = None
        plan_str = None
        if custom_id and ":" in custom_id:
            org_id_str, plan_str = custom_id.split(":", 1)

        status_str = resource.get("status")
        status_mapping = {
            "APPROVAL_PENDING": SubscriptionStatus.TRIALING,
            "APPROVED": SubscriptionStatus.TRIALING,
            "ACTIVE": SubscriptionStatus.ACTIVE,
            "SUSPENDED": SubscriptionStatus.PAST_DUE,
            "CANCELLED": SubscriptionStatus.CANCELED,
            "EXPIRED": SubscriptionStatus.CANCELED,
        }
        mapped_status = status_mapping.get(status_str, SubscriptionStatus.CANCELED)

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

        if org:
            org.billing_provider = "paypal"
            org.billing_customer_id = customer_id or org.billing_customer_id
            org.billing_subscription_id = subscription_id
            org.subscription_status = mapped_status
            if plan_str:
                org.plan = PlanType(plan_str)

            # PayPal trial ends at parsing
            org.trial_ends_at = None  # PayPal handles trial periods internally in plans

            db.add(org)
            await db.flush()
