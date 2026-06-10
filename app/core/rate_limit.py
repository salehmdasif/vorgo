import logging
from uuid import UUID

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis-backed rate limiting setup
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
)

RATE_LIMITS = {
    "free": "100/hour",
    "pro": "1000/hour",
    "enterprise": "10000/hour",
}


async def dynamic_rate_limit(request: Request) -> str:
    """
    Resolves the appropriate rate limit string based on the user's organization plan.
    Uses Redis caching to avoid database queries on every HTTP request.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return "20/minute"

    token = auth_header.split(" ")[1]
    try:
        from app.core.redis import get_redis_pool
        from app.core.security.jwt import verify_token

        # Verify access token signature and get user ID
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return "20/minute"

        redis = await get_redis_pool()
        cache_key = f"user_plan:{user_id}"
        
        # 1. Attempt to get plan from Redis cache
        cached_plan = await redis.get(cache_key)
        if cached_plan:
            plan = cached_plan.decode() if isinstance(cached_plan, bytes) else cached_plan
            return RATE_LIMITS.get(plan, "100/hour")

        # 2. Database lookup on cache miss
        from app.core.database import get_db_context
        from app.models.organization import Organization
        from app.models.user import User

        async with get_db_context() as db:
            stmt = select(User.org_id).where(User.id == UUID(user_id))
            res = await db.execute(stmt)
            org_id = res.scalar_one_or_none()

            if org_id:
                stmt_org = select(Organization.plan).where(Organization.id == org_id)
                res_org = await db.execute(stmt_org)
                plan_enum = res_org.scalar_one_or_none()
                if plan_enum:
                    plan = plan_enum.value
                    # Cache in Redis for 10 minutes (600 seconds)
                    await redis.setex(cache_key, 600, plan)
                    return RATE_LIMITS.get(plan, "100/hour")
    except Exception as e:
        logger.error(f"Failed to evaluate dynamic rate limit: {e}")

    # Default fallback limit for authenticated users
    return "100/hour"
