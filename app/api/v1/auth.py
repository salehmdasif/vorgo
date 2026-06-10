# ── Imports ───────────────────────────────────────────────────────────────────
from typing import Any, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user, fastapi_users, get_user_manager, UserManager
from app.core.database import get_db
from app.core.exceptions import Errors
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    create_pre_2fa_token,
    verify_token,
)
from app.core.security.tokens import (
    refresh_token_exists,
    revoke_all_refresh_tokens,
    rotate_refresh_token,
    store_refresh_token,
)
from app.core.security.two_factor import (
    decrypt_secret,
    encrypt_secret,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_uri,
    verify_and_use_backup_code,
    verify_totp_code,
)
from app.models.user import User
from app.schemas.auth import (
    LoginResponse2FA,
    RefreshRequest,
    TokenResponse,
    TwoFactorChallengeRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
)
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

# ── fastapi-users routes ──────────────────────────────────────────────────────

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


# ── Custom Auth Endpoints ─────────────────────────────────────────────────────


@router.post(
    "/auth/login",
    response_model=Union[TokenResponse, LoginResponse2FA],
    tags=["Auth"],
    summary="Login with password",
)
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
) -> Any:
    """
    Standard OAuth2 password login.
    If 2FA is enabled, returns requires_2fa status and a pre_2fa token.
    Otherwise, returns access + refresh tokens.
    """
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS",
        )

    if user.totp_enabled:
        pre_2fa_token = create_pre_2fa_token(str(user.id))
        return LoginResponse2FA(pre_2fa_token=pre_2fa_token)

    refresh_token, jti = create_refresh_token(str(user.id))
    await store_refresh_token(str(user.id), jti)
    access_token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
    summary="Logout current session",
)
async def logout(user: User = Depends(current_active_user)) -> None:
    """Logout current session (stateless - client discards access token)."""
    pass


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


# ── Two-Factor Authentication (2FA) Endpoints ─────────────────────────────────


@router.get(
    "/auth/2fa/setup",
    response_model=TwoFactorSetupResponse,
    tags=["Auth"],
    summary="Get 2FA setup details",
)
async def setup_two_factor(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorSetupResponse:
    """Generates a random secret and provisioning URI for 2FA setup."""
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user.email)

    # Save encrypted secret to the user model temporarily
    user.totp_secret = encrypt_secret(secret)
    db.add(user)

    return TwoFactorSetupResponse(
        secret=secret,
        provisioning_uri=uri,
    )


@router.post(
    "/auth/2fa/verify",
    response_model=TwoFactorVerifyResponse,
    tags=["Auth"],
    summary="Verify 2FA setup and enable it",
)
async def verify_two_factor(
    body: TwoFactorVerifyRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorVerifyResponse:
    """Verifies the 6-digit TOTP code. If valid, enables 2FA and returns 8 backup codes."""
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA_NOT_SETUP",
        )

    secret = decrypt_secret(user.totp_secret)
    if not verify_totp_code(secret, body.code):
        raise Errors.INVALID_2FA_CODE()

    plain_backup, hashed_backup = generate_backup_codes()
    user.totp_enabled = True
    user.backup_codes = hashed_backup
    db.add(user)

    return TwoFactorVerifyResponse(
        backup_codes=plain_backup,
    )


@router.post(
    "/auth/2fa/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
    summary="Disable 2FA",
)
async def disable_two_factor(
    body: TwoFactorVerifyRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Disables 2FA. Requires a valid 6-digit TOTP code for verification."""
    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA_NOT_ENABLED",
        )

    secret = decrypt_secret(user.totp_secret)
    if not verify_totp_code(secret, body.code):
        raise Errors.INVALID_2FA_CODE()

    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = []
    db.add(user)


@router.post(
    "/auth/2fa/challenge",
    response_model=TokenResponse,
    tags=["Auth"],
    summary="Submit 2FA code during login",
)
async def challenge_two_factor(
    body: TwoFactorChallengeRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Verifies a 2FA code or backup code using a pre_2fa token."""
    try:
        data = verify_token(body.pre_2fa_token)
    except Exception:
        raise Errors.UNAUTHORIZED()

    if data.get("type") != "pre_2fa":
        raise Errors.UNAUTHORIZED()

    user_id = data.get("sub")
    if not user_id:
        raise Errors.UNAUTHORIZED()

    # Load user
    stmt = select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.totp_enabled or not user.totp_secret:
        raise Errors.UNAUTHORIZED()

    # Check if code is a 6-digit TOTP code
    is_valid = False
    if len(body.code) == 6 and body.code.isdigit():
        secret = decrypt_secret(user.totp_secret)
        is_valid = verify_totp_code(secret, body.code)
    else:
        # Check backup code
        is_valid, updated_backup = verify_and_use_backup_code(
            user.backup_codes, body.code
        )
        if is_valid:
            user.backup_codes = updated_backup
            db.add(user)

    if not is_valid:
        raise Errors.INVALID_2FA_CODE()

    # Issue full tokens
    refresh_token, jti = create_refresh_token(str(user.id))
    await store_refresh_token(str(user.id), jti)
    access_token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
