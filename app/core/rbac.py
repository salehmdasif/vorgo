from collections.abc import Callable
from fastapi import Depends

from app.core.auth import current_active_user
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
