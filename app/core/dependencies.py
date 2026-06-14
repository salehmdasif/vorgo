from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user, current_superuser, current_verified_user
from app.core.database import get_db, get_db_context
from app.core.exceptions import Errors
from app.core.redis import get_redis
from app.core.security.jwt import verify_token
from app.core.tenancy.service import AdminTenantService, TenantService
from app.models.user import User


async def get_tenant_service(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
) -> TenantService:
    """
    Injects a TenantService scoped to the current user's org.
    Raises FORBIDDEN if user has no org (e.g. super_admin without org).
    """
    if not user.org_id:
        raise Errors.FORBIDDEN()
    return TenantService(db=db, org_id=user.org_id)


async def get_admin_tenant_service(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_active_user),
) -> AdminTenantService:
    """No org_id filter - super_admin only. Guard with require_superuser() on the route."""
    if not user.is_superuser:
        raise Errors.FORBIDDEN()
    return AdminTenantService(db=db)


async def get_current_user_from_cookie_or_header(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User | None:
    """Resolves the current active user from either Authorization header or cookies."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        token = request.cookies.get("fastapiusersauth") or request.cookies.get(
            "access_token"
        )

    if not token:
        return None

    try:
        payload = verify_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        stmt = select(User).where(User.id == UUID(user_id), User.is_active)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
    except Exception:
        return None


async def require_dashboard_user(
    user: User | None = Depends(get_current_user_from_cookie_or_header),
) -> User:
    """Guards dashboard routes. Redirects to /login if no valid token is found."""
    if not user:
        # Raise HTTP 401 which will be handled or return RedirectResponse
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"},
        )
    return user


async def get_dashboard_tenant_service(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dashboard_user),
) -> TenantService:
    """Injects a TenantService scoped to the dashboard user's org."""
    if not user.org_id:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/dashboard/setup-org"},
        )
    return TenantService(db=db, org_id=user.org_id)


__all__ = [
    "get_db",
    "get_db_context",
    "get_redis",
    "current_active_user",
    "current_verified_user",
    "current_superuser",
    "get_tenant_service",
    "get_admin_tenant_service",
    "get_current_user_from_cookie_or_header",
    "require_dashboard_user",
    "get_dashboard_tenant_service",
]
