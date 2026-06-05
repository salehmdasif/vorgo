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
        # TODO: send welcome email (Commit 14)
        # TODO: create default Organization and set user.org_id
        pass

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        # TODO: send password reset email (Commit 14)
        pass

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        # TODO: send email verification link (Commit 14)
        pass


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
