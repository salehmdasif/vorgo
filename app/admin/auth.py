# ── Imports ───────────────────────────────────────────────────────────────────
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.auth import UserManager
from app.core.database import AsyncSessionLocal
from app.models.user import User

# ── Credentials Helper ────────────────────────────────────────────────────────


class SimpleCredentials:
    """Helper class to match fastapi-users authenticate credentials argument."""

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password


# ── Authentication Backend ────────────────────────────────────────────────────


class AdminAuth(AuthenticationBackend):
    """
    SQLAdmin Authentication Backend.
    Restricts access to active superusers.
    Stores user ID in Starlette session cookie.
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))

        if not username or not password:
            return False

        async with AsyncSessionLocal() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)
            try:
                credentials = SimpleCredentials(username=username, password=password)
                user = await user_manager.authenticate(credentials)  # type: ignore[arg-type]
                if user and user.is_superuser and user.is_active:
                    request.session.update({"token": str(user.id)})
                    return True
            except Exception:
                pass
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(
                User.id == token,
                User.is_superuser == True,  # noqa: E712
                User.is_active == True,  # noqa: E712
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return True
        return False
