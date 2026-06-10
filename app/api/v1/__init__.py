from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.system import router as system_router
from app.api.v1.users import router as users_router
from app.api.v1.invitations import router as invitations_router
from app.webhooks.stripe import router as stripe_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(billing_router)
api_router.include_router(invitations_router)
api_router.include_router(stripe_router)

