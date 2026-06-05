from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

_redis_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    """Returns the module-level Redis pool, creating it on first call."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency — yields the shared Redis pool."""
    pool = await get_redis_pool()
    yield pool


async def check_redis_connection() -> bool:
    """Returns False if Redis is unreachable. App continues in degraded mode."""
    try:
        pool = await get_redis_pool()
        await pool.ping()
        return True
    except Exception:
        return False


async def close_redis_pool() -> None:
    """Called on app shutdown after engine.dispose()."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
