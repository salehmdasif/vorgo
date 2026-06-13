from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.billing.stripe import StripeBillingService
from app.services.billing.lemon import LemonSqueezyBillingService
from app.services.billing.paypal import PayPalBillingService
from app.services.billing.payoneer import PayoneerBillingService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Receives and processes raw Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    try:
        service = StripeBillingService()
        await service.handle_webhook(db, payload, sig_header)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/lemonsqueezy", status_code=status.HTTP_200_OK)
async def lemonsqueezy_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Receives and processes Lemon Squeezy webhook events."""
    payload = await request.body()
    signature = request.headers.get("x-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing x-signature header",
        )

    try:
        service = LemonSqueezyBillingService()
        await service.handle_webhook(db, payload, signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/paypal", status_code=status.HTTP_200_OK)
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Receives and processes PayPal webhook events."""
    payload = await request.body()
    # PayPal sends transmission signatures in multiple headers: paypal-transmission-id, etc.
    # In sandbox/dev we check for basic processing. We pass transmission id or headers as signature.
    signature = request.headers.get("paypal-transmission-id", "mock-sig")

    try:
        service = PayPalBillingService()
        await service.handle_webhook(db, payload, signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/payoneer", status_code=status.HTTP_200_OK)
async def payoneer_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Receives and processes Payoneer IPN events."""
    payload = await request.body()
    signature = request.headers.get("x-payoneer-signature", "mock-sig")

    try:
        service = PayoneerBillingService()
        await service.handle_webhook(db, payload, signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
