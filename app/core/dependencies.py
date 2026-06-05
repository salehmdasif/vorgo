from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis

# TODO: Commit 3+ — current_user, tenant_service dependencies যোগ হবে

__all__ = ["get_db", "get_redis"]
