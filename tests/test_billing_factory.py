import pytest
from app.core.config import settings
from app.services.billing.factory import get_billing_service
from app.services.billing.stripe import StripeBillingService
from app.services.billing.lemon import LemonSqueezyBillingService
from app.services.billing.paypal import PayPalBillingService
from app.services.billing.payoneer import PayoneerBillingService

def test_billing_service_factory():
    # Test Stripe
    settings.BILLING_PROVIDER = "stripe"
    service = get_billing_service()
    assert isinstance(service, StripeBillingService)

    # Test Lemon Squeezy
    settings.BILLING_PROVIDER = "lemonsqueezy"
    service = get_billing_service()
    assert isinstance(service, LemonSqueezyBillingService)

    # Test PayPal
    settings.BILLING_PROVIDER = "paypal"
    service = get_billing_service()
    assert isinstance(service, PayPalBillingService)

    # Test Payoneer
    settings.BILLING_PROVIDER = "payoneer"
    service = get_billing_service()
    assert isinstance(service, PayoneerBillingService)

    # Test Invalid
    settings.BILLING_PROVIDER = "invalid"
    with pytest.raises(ValueError):
        get_billing_service()
