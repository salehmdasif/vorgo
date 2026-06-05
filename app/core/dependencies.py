from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db, get_db_context
from app.core.redis import get_redis
from app.core.auth import current_active_user, current_verified_user, current_superuser
from app.core.tenancy.service import TenantService, AdminTenantService
from app.core.exceptions import Errors
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
    """No org_id filter — super_admin only. Guard with require_superuser() on the route."""
    if not user.is_superuser:
        raise Errors.FORBIDDEN()
    return AdminTenantService(db=db)


__all__ = [
    "get_db",
    "get_db_context",
    "get_redis",
    "current_active_user",
    "current_verified_user",
    "current_superuser",
    "get_tenant_service",
    "get_admin_tenant_service",
]
