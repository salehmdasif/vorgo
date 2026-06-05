from typing import Any, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Errors
from app.models.base import Base


class TenantService:
    """
    All DB queries go through here for tenant-scoped models.
    org_id filter is applied automatically — direct queries risk data leaks.

    Usage in a route:
        tenant = Depends(get_tenant_service)
        items = await tenant.get_all(Product)
        item  = await tenant.get_one(Product, item_id)
    """

    def __init__(self, db: AsyncSession, org_id: UUID) -> None:
        self.db = db
        self.org_id = org_id

    async def get_all(
        self,
        model: Type[Base],
        order_by=None,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> list:
        stmt = select(model).where(
            model.org_id == self.org_id,  # type: ignore[attr-defined]
            *[getattr(model, k) == v for k, v in filters.items()],
        )
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_one(self, model: Type[Base], record_id: UUID) -> Any:
        stmt = select(model).where(
            model.org_id == self.org_id,  # type: ignore[attr-defined]
            model.id == record_id,  # type: ignore[attr-defined]
        )
        result = await self.db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise Errors.NOT_FOUND(model.__name__)
        return obj

    async def get_by(self, model: Type[Base], **filters: Any) -> Any:
        """get_one by arbitrary field instead of id."""
        stmt = select(model).where(
            model.org_id == self.org_id,  # type: ignore[attr-defined]
            *[getattr(model, k) == v for k, v in filters.items()],
        )
        result = await self.db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise Errors.NOT_FOUND(model.__name__)
        return obj

    async def create(self, model: Type[Base], **data: Any) -> Any:
        obj = model(org_id=self.org_id, **data)  # type: ignore[call-arg]
        self.db.add(obj)
        await self.db.flush()  # get id without committing — session commits at request end
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Any, **data: Any) -> Any:
        for field, value in data.items():
            setattr(obj, field, value)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Any) -> None:
        await self.db.delete(obj)
        await self.db.flush()

    async def count(self, model: Type[Base], **filters: Any) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(model).where(
            model.org_id == self.org_id,  # type: ignore[attr-defined]
            *[getattr(model, k) == v for k, v in filters.items()],
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()


class AdminTenantService:
    """
    Super admin use only — no org_id filter.
    All orgs' data is visible.
    Guard with require_superuser() before injecting this.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, model: Type[Base], **filters: Any) -> list:
        stmt = select(model).where(
            *[getattr(model, k) == v for k, v in filters.items()],
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_one(self, model: Type[Base], record_id: UUID) -> Any:
        stmt = select(model).where(model.id == record_id)  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise Errors.NOT_FOUND(model.__name__)
        return obj
