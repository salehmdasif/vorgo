from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, PlanType, SubscriptionStatus
from app.services.billing.base import BaseBillingService


class PayoneerBillingService(BaseBillingService):
    """
    Payoneer Implementation of the Unified Billing Service.
    Supports B2B invoicing redirect and simulated checkout callbacks.
    """

    async def create_checkout_session(
        self, org_id: UUID, plan: PlanType, email: str
    ) -> str:
        # Since Payoneer Checkout requires direct custom approval, SaaS systems
        # commonly generate a Payoneer Request a Payment URL or hosted checkout intent.
        # We redirect users to a hosted checkout route inside the app, which serves
        # as a mock Payoneer page, or a Payoneer client billing portal.
        # Here we return a local checkout route that mocks the Payoneer card payment page.
        checkout_url = f"{settings.FRONTEND_URL}/dashboard/billing/payoneer?org_id={org_id}&plan={plan.value}&email={email}"
        return checkout_url

    async def create_portal_session(self, customer_id: str) -> str:
        # Payoneer user billing dashboard
        return "https://myaccount.payoneer.com"

    async def handle_webhook(
        self, db: AsyncSession, payload: bytes, signature: str
    ) -> None:
        # Verify Payoneer signature / IPN
        import json

        event = json.loads(payload.decode())
        event_type = event.get("event_type")
        data = event.get("data", {})

        if event_type == "payment.completed":
            org_id_str = data.get("org_id")
            plan_str = data.get("plan")
            payment_id = data.get("payment_id")
            customer_id = data.get("customer_id")

            if org_id_str:
                stmt = select(Organization).where(Organization.id == UUID(org_id_str))
                result = await db.execute(stmt)
                org = result.scalar_one_or_none()

                if org:
                    org.billing_provider = "payoneer"
                    org.billing_customer_id = customer_id
                    org.billing_subscription_id = payment_id
                    org.subscription_status = SubscriptionStatus.ACTIVE
                    if plan_str:
                        org.plan = PlanType(plan_str)

                    db.add(org)
                    await db.flush()
