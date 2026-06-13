from app.core.config import settings
from app.services.billing.base import BaseBillingService
from app.services.billing.stripe import StripeBillingService
from app.services.billing.lemon import LemonSqueezyBillingService
from app.services.billing.paypal import PayPalBillingService
from app.services.billing.payoneer import PayoneerBillingService

def get_billing_service() -> BaseBillingService:
    """Returns the instantiated active Billing Service based on APP settings."""
    provider = settings.BILLING_PROVIDER.lower().strip()
    
    if provider == "stripe":
        return StripeBillingService()
    elif provider in ["lemonsqueezy", "lemon_squeezy"]:
        return LemonSqueezyBillingService()
    elif provider == "paypal":
        return PayPalBillingService()
    elif provider == "payoneer":
        return PayoneerBillingService()
    else:
        raise ValueError(f"Unknown billing provider configured: {settings.BILLING_PROVIDER}")
