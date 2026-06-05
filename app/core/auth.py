import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from app.core.security.jwt import ED25519JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        # TODO: Commit 6 — welcome email পাঠাও
        # TODO: default Organization তৈরি করো, user.org_id set করো
        pass

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        # TODO: Commit 6 — password reset link সহ email পাঠাও
        pass

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        # TODO: Commit 6 — email verification link সহ email পাঠাও
        pass


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# ── Auth Backend ──────────────────────────────────────────────────────────────
# Commit 4: temporary HS256 JWT — functional কিন্তু production-ready না
# Commit 5: get_jwt_strategy() এ ED25519JWTStrategy দিয়ে replace হবে
# transport আর backend এর বাকি সব same থাকবে — শুধু strategy বদলাবে

bearer_transport = BearerTransport(tokenUrl="/api/v1/auth/login")


def get_jwt_strategy() -> ED25519JWTStrategy:
    return ED25519JWTStrategy()


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ── FastAPIUsers instance ─────────────────────────────────────────────────────
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# ── Current user dependencies ─────────────────────────────────────────────────
# route এ Depends() দিয়ে use করো
# from app.core.auth import current_active_user
current_active_user = fastapi_users.current_user(active=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
