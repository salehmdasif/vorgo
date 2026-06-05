from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

# module-level pool - app lifetime এ একটাই instance থাকবে
# প্রতি request এ নতুন connection না নিয়ে pool থেকে নেওয়া হয়
_redis_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        # decode_responses=True - bytes এর বদলে str পাওয়া যাবে
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    # FastAPI Depends() এ use করো
    # NOTE: Redis connection pool এ close করার দরকার নেই - pool manage করে
    pool = await get_redis_pool()
    yield pool


async def check_redis_connection() -> bool:
    # startup health check আর /health endpoint দুটোতেই use হয়
    # Redis down থাকলে rate limiting আর token revocation silently skip হবে
    # app crash করবে না - degraded mode এ চলবে
    try:
        pool = await get_redis_pool()
        await pool.ping()
        return True
    except Exception:
        return False


async def close_redis_pool() -> None:
    # app shutdown এ engine.dispose() এর পরে call করো
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
