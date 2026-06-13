import hmac
import hashlib
import httpx
from datetime import datetime, UTC
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, PlanType, SubscriptionStatus
from app.services.billing.base import BaseBillingService

class LemonSqueezyBillingService(BaseBillingService):
    """Lemon Squeezy Implementation of the Unified Billing Service."""

    def _get_variant_id_for_plan(self, plan: PlanType) -> str:
        mapping = {
            PlanType.FREE: settings.LEMON_SQUEEZY_FREE_PRICE_ID,
            PlanType.PRO: settings.LEMON_SQUEEZY_PRO_PRICE_ID,
            PlanType.ENTERPRISE: settings.LEMON_SQUEEZY_ENTERPRISE_PRICE_ID,
        }
        variant_id = mapping.get(plan)
        if not variant_id:
            raise ValueError(f"Lemon Squeezy Variant ID not configured for plan: {plan}")
        return variant_id

    async def create_checkout_session(
        self, org_id: UUID, plan: PlanType, email: str
    ) -> str:
        variant_id = self._get_variant_id_for_plan(plan)
        
        # Call Lemon Squeezy API to create checkout
        async with httpx.AsyncClient() as client:
            headers = {
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
                "Authorization": f"Bearer {settings.LEMON_SQUEEZY_API_KEY}"
            }
            
            payload = {
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "checkout_data": {
                            "email": email,
                            "custom": {
                                "org_id": str(org_id),
                                "plan": plan.value
                            }
                        }
                    },
                    "relationships": {
                        "store": {
                            "data": {
                                "type": "stores",
                                "id": "1"  # Replace with actual store ID or retrieve dynamically
                            }
                        },
                        "variant": {
                            "data": {
                                "type": "variants",
                                "id": str(variant_id)
                            }
                        }
                    }
                }
            }
            
            # Post to checkout creation endpoint
            # Note: For simplicity, Lemon Squeezy supports direct checkout links:
            # https://[store-slug].lemonsqueezy.com/checkout/buy/[variant-id]?checkout[email]=[email]&checkout[custom][org_id]=[org_id]
            # This is simpler and doesn't require store ID configuration!
            # Let's generate the direct checkout URL to reduce API overhead and setup complexity.
            store_url = f"https://vorgo.lemonsqueezy.com/checkout/buy/{variant_id}"
            checkout_url = f"{store_url}?checkout[email]={email}&checkout[custom][org_id]={org_id}&checkout[custom][plan]={plan.value}&embed=1"
            return checkout_url

    async def create_portal_session(self, customer_id: str) -> str:
        # Lemon Squeezy handles customer portal directly via their dashboard or hosted link.
        # We redirect users to Lemon Squeezy's default billing dashboard url.
        return "https://my.lemonsqueezy.com/billing"

    async def handle_webhook(
        self, db: AsyncSession, payload: bytes, signature: str
    ) -> None:
        # Verify Lemon Squeezy signature using HMAC-SHA256
        secret = settings.LEMON_SQUEEZY_WEBHOOK_SECRET.encode()
        digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid Lemon Squeezy signature verification")

        import json
        event = json.loads(payload.decode())
        event_name = event.get("meta", {}).get("event_name")
        data = event.get("data", {})

        if event_name in [
            "subscription_created",
            "subscription_updated",
            "subscription_cancelled",
            "subscription_resumed",
            "subscription_expired",
        ]:
            await self._process_subscription_change(db, event_name, data)

    async def _process_subscription_change(
        self, db: AsyncSession, event_name: str, data: dict[str, Any]
    ) -> None:
        attrs = data.get("attributes", {})
        subscription_id = str(data.get("id"))
        customer_id = str(attrs.get("customer_id"))
        
        custom_data = event_name == "subscription_created" and attrs.get("first_subscription_item", {}).get("subscription_id")
        # Custom parameters passed during checkout are returned in meta -> custom_data
        meta = data.get("meta", {}) if data.get("meta") else {}
        # In Lemon Squeezy webhooks, custom data is stored in event['meta']['custom_data']
        # Let's handle it properly
        custom_fields = attrs.get("custom_data", {})
        if not custom_fields:
            # Fallback if in metadata
            custom_fields = meta.get("custom_data", {})

        org_id_str = custom_fields.get("org_id")
        plan_str = custom_fields.get("plan")

        status_str = attrs.get("status")
        status_mapping = {
            "on_trial": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "unpaid": SubscriptionStatus.UNPAID,
            "cancelled": SubscriptionStatus.CANCELED,
            "expired": SubscriptionStatus.CANCELED,
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
            org.billing_provider = "lemonsqueezy"
            org.billing_customer_id = customer_id
            org.billing_subscription_id = subscription_id
            org.subscription_status = mapped_status
            if plan_str:
                org.plan = PlanType(plan_str)

            trial_ends_at = attrs.get("trial_ends_at")
            if trial_ends_at:
                try:
                    org.trial_ends_at = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
                except Exception:
                    org.trial_ends_at = None
            else:
                org.trial_ends_at = None

            db.add(org)
            await db.flush()
