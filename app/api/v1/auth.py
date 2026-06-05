from fastapi import APIRouter, Depends, status

from app.core.auth import auth_backend, current_active_user, fastapi_users
from app.core.exceptions import Errors
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.security.tokens import (
    refresh_token_exists,
    revoke_all_refresh_tokens,
    rotate_refresh_token,
    store_refresh_token,
)
from app.models.user import User
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

# POST /auth/login  → access token
# POST /auth/logout → client discards token (stateless)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/register
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/request-verify-token
# POST /auth/verify
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"],
)

# POST /auth/forgot-password
# POST /auth/reset-password
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)


# ── Custom endpoints ──────────────────────────────────────────────────────────


@router.post(
    "/auth/token",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Login and get access + refresh tokens",
)
async def login_with_refresh(
    user: User = Depends(current_active_user),
) -> TokenResponse:
    """
    Called after /auth/login succeeds.
    Issues a refresh token and stores it in Redis.
    Flow: client calls /auth/login first, then this endpoint to get the refresh token.
    """
    refresh_token, jti = create_refresh_token(str(user.id))
    await store_refresh_token(str(user.id), jti)
    access_token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Rotate refresh token",
)
async def refresh_tokens(body: RefreshRequest) -> TokenResponse:
    """
    Refresh token rotation.
    - Verifies signature
    - Checks Redis (reuse detection)
    - Deletes old token, issues new access + refresh tokens
    - If token not in Redis: reuse detected, all sessions revoked
    """
    try:
        data = verify_token(body.refresh_token)
    except Exception:
        raise Errors.UNAUTHORIZED()

    if data.get("type") != "refresh":
        raise Errors.UNAUTHORIZED()

    user_id = data.get("sub")
    old_jti = data.get("jti")

    if not user_id or not old_jti:
        raise Errors.UNAUTHORIZED()

    exists = await refresh_token_exists(user_id, old_jti)

    if not exists:
        # Reuse detected - token was already rotated, possible theft
        await revoke_all_refresh_tokens(user_id)
        raise Errors.TOKEN_REUSE_DETECTED()

    new_refresh_token, new_jti = create_refresh_token(user_id)
    await rotate_refresh_token(user_id, old_jti, new_jti)
    new_access_token = create_access_token(user_id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.post(
    "/auth/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
    summary="Logout all devices",
)
async def logout_all_devices(
    user: User = Depends(current_active_user),
) -> None:
    """Revokes all refresh tokens for this user - logs out every device."""
    await revoke_all_refresh_tokens(str(user.id))
