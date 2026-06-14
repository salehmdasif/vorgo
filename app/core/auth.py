import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError, Errors
from app.core.redis import get_redis_pool
from app.core.security.jwt import ED25519JWTStrategy
from app.models.user import User

_LOCKOUT_MAX_ATTEMPTS = 5
_LOCKOUT_TTL_SECONDS = 15 * 60  # 15 minutes


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    def __init__(self, user_db, password_helper=None):
        if password_helper is None:
            from fastapi_users.password import PasswordHelper

            from app.core.security.hashing import pwd_context

            password_helper = PasswordHelper(pwd_context)
        super().__init__(user_db, password_helper)

    async def authenticate(self, credentials):
        email = credentials.username.lower()
        lockout_key = f"lockout:{email}"
        try:
            redis = await get_redis_pool()
            attempts = await redis.get(lockout_key)
            if attempts and int(attempts) >= _LOCKOUT_MAX_ATTEMPTS:
                raise Errors.ACCOUNT_LOCKED()
            user = await super().authenticate(credentials)
            if user is None:
                await redis.incr(lockout_key)
                await redis.expire(lockout_key, _LOCKOUT_TTL_SECONDS)
            else:
                await redis.delete(lockout_key)
            return user
        except Exception as exc:
            if isinstance(exc, AppError):
                raise
            return await super().authenticate(credentials)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import select

        from app.core.database import get_db_context
        from app.models.organization import Organization, PlanType, SubscriptionStatus
        from app.models.user import UserRole
        from app.services.email_service import email_service

        async with get_db_context() as db:
            stmt = select(User).where(User.id == user.id)
            res = await db.execute(stmt)
            db_user = res.scalar_one()

            if not db_user.org_id:
                org_name = f"{db_user.email.split('@')[0]}'s Workspace"
                slug_base = db_user.email.split("@")[0].lower()
                org = Organization(
                    name=org_name,
                    slug=f"{slug_base}-{uuid.uuid4().hex[:6]}",
                    plan=PlanType.FREE,
                    subscription_status=SubscriptionStatus.TRIALING,
                    trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
                    is_active=True,
                )
                db.add(org)
                await db.commit()
                await db.refresh(org)

                db_user.org_id = org.id
                db_user.role = UserRole.ADMIN
                await db.commit()

        await email_service.send_email(
            to_email=user.email,
            subject="Welcome to Vorgo",
            template_name="welcome.html",
            context={"user_name": user.email},
        )

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        from app.services.email_service import email_service

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await email_service.send_email(
            to_email=user.email,
            subject="Reset Your Password",
            template_name="reset_password.html",
            context={"reset_link": reset_link},
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        from app.services.email_service import email_service

        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        await email_service.send_email(
            to_email=user.email,
            subject="Verify Your Email",
            template_name="verify.html",
            context={"verify_link": verify_link},
        )


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/api/v1/auth/login")


def get_jwt_strategy() -> ED25519JWTStrategy:
    return ED25519JWTStrategy()


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
