from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import PlanType

class BaseBillingService:
    """Interface for SaaS Billing integration (Stripe, Lemon Squeezy, PayPal, Payoneer)."""

    async def create_checkout_session(
        self, org_id: UUID, plan: PlanType, email: str
    ) -> str:
        """Creates a checkout session/payment link and returns the checkout URL."""
        raise NotImplementedError()

    async def create_portal_session(self, customer_id: str) -> str:
        """Creates a billing portal session and returns its URL."""
        raise NotImplementedError()

    async def handle_webhook(
        self, db: AsyncSession, payload: bytes, signature: str
    ) -> None:
        """Processes gateway webhooks and updates subscription statuses in the database."""
        raise NotImplementedError()
