# ── Imports ───────────────────────────────────────────────────────────────────
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_pool
from app.models.feature_flag import FeatureFlag
from app.models.organization import PlanType

# ── Redis Key Pattern ─────────────────────────────────────────────────────────
# Key: ff:{name}
# TTL: 10 minutes (600 seconds)

# ── Feature Evaluation ────────────────────────────────────────────────────────


async def is_feature_enabled(
    db: AsyncSession,
    name: str,
    org_id: UUID | None = None,
    plan: PlanType | None = None,
) -> bool:
    """
    Checks if a feature flag is enabled for the given tenant context.
    Uses Redis cache to prevent database bottlenecks.
    """
    flag_data = None
    redis_key = f"ff:{name}"

    # 1. Attempt to read from Redis cache
    try:
        redis = await get_redis_pool()
        cached = await redis.get(redis_key)
        if cached:
            flag_data = json.loads(cached)
    except Exception:
        # Fallback to database on Redis connection failure
        pass

    # 2. Database lookup on cache miss
    if flag_data is None:
        stmt = select(FeatureFlag).where(FeatureFlag.name == name)
        result = await db.execute(stmt)
        flag = result.scalar_one_or_none()

        if not flag:
            return False

        flag_data = {
            "enabled_globally": flag.enabled_globally,
            "enabled_for_plans": flag.enabled_for_plans,
            "enabled_for_orgs": [str(org) for org in flag.enabled_for_orgs],
        }

        # 3. Write back to Redis cache (expires in 10 minutes)
        try:
            redis = await get_redis_pool()
            await redis.setex(redis_key, 600, json.dumps(flag_data))
        except Exception:
            pass

    # 4. Check feature flag evaluation rules
    if flag_data["enabled_globally"]:
        return True

    if org_id and str(org_id) in flag_data["enabled_for_orgs"]:
        return True

    if plan and plan.value in flag_data["enabled_for_plans"]:
        return True

    return False


async def invalidate_feature_flag_cache(name: str) -> None:
    """Clears the cached evaluation rule for a feature flag."""
    try:
        redis = await get_redis_pool()
        await redis.delete(f"ff:{name}")
    except Exception:
        pass
