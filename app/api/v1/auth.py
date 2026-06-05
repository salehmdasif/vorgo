from fastapi import APIRouter

from app.core.auth import fastapi_users, auth_backend
from app.schemas.user import UserRead, UserCreate

router = APIRouter()

# POST /auth/login  → Bearer token return করে
# POST /auth/logout → token invalidate করে (Commit 5 এ Redis revocation যোগ হবে)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/register → user তৈরি করে, on_after_register trigger হয়
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/request-verify-token → verification email resend করে
# POST /auth/verify                → token দিয়ে email verify করে
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/forgot-password → reset token email পাঠায়
# POST /auth/reset-password  → token + new password দিয়ে reset করে
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)
