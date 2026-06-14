from collections.abc import Callable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_db
from app.core.exceptions import Errors
from app.models.user import User, UserRole


def require_role(*roles: UserRole) -> Callable:
    """
    Checks that the current user has one of the given system roles.
    super_admin always passes regardless of roles listed.

    Usage:
        @router.get("/admin/stats")
        async def stats(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if user.is_superuser:
            return user
        if user.role not in roles:
            raise Errors.FORBIDDEN()
        return user

    return dependency


def require_superuser() -> Callable:
    """Only super_admin (is_superuser=True) can access."""

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if not user.is_superuser:
            raise Errors.FORBIDDEN()
        return user

    return dependency


def require_verified() -> Callable:
    """User must have verified their email."""

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if not user.is_verified:
            raise Errors.FORBIDDEN()
        return user

    return dependency


def require_feature(name: str) -> Callable:
    """
    Returns a FastAPI dependency to gate access by feature flag.
    Requires that the current user's organization has access to the feature flag.
    Super admin bypasses feature flags checks.
    """

    async def dependency(
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_active_user),
    ) -> None:
        if user.is_superuser:
            return

        if not user.org_id:
            raise Errors.FORBIDDEN()

        # Load organization to check plan
        from app.models.organization import Organization

        stmt = select(Organization).where(Organization.id == user.org_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()

        if not org or not org.is_active:
            raise Errors.FORBIDDEN()

        # Evaluate feature flag using the service layer
        from app.services.feature_flag_service import is_feature_enabled

        enabled = await is_feature_enabled(
            db=db,
            name=name,
            org_id=user.org_id,
            plan=org.plan,
        )
        if not enabled:
            raise Errors.PLAN_LIMIT_EXCEEDED()

    return dependency
