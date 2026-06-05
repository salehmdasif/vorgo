import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis import get_redis_pool


# Redis key pattern: rt:{user_id}:{jti}
# TTL = REFRESH_TOKEN_EXPIRE_DAYS

def _key(user_id: str, jti: str) -> str:
    return f"rt:{user_id}:{jti}"


async def store_refresh_token(user_id: str, jti: str) -> None:
    """Called after issuing a new refresh token."""
    redis = await get_redis_pool()
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.setex(_key(user_id, jti), ttl, "1")


async def refresh_token_exists(user_id: str, jti: str) -> bool:
    """Returns True if the token is valid (not yet rotated or revoked)."""
    redis = await get_redis_pool()
    return await redis.exists(_key(user_id, jti)) == 1


async def rotate_refresh_token(
    user_id: str, old_jti: str, new_jti: str
) -> None:
    """Atomically deletes old token and stores new token."""
    redis = await get_redis_pool()
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    pipe = redis.pipeline()
    pipe.delete(_key(user_id, old_jti))
    pipe.setex(_key(user_id, new_jti), ttl, "1")
    await pipe.execute()


async def revoke_all_refresh_tokens(user_id: str) -> None:
    """
    Logout all devices — deletes every refresh token for this user.
    Called on: token reuse detected, manual logout-all, password change.
    """
    redis = await get_redis_pool()
    pattern = f"rt:{user_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
