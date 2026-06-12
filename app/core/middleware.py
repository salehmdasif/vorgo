import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import get_db_context
from app.core.redis import get_redis_pool
from app.models.organization import Organization


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique UUID into every request for tracing in logs and Sentry."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets security headers on every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response


logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resolves the organization tenant from the request host subdomain.
    Caches resolved tenant IDs in Redis for 1 hour to prevent DB load.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.models.user import User
        from app.core.security.jwt import verify_token

        host = request.headers.get("host", "")
        host_name = host.split(":")[0]
        parts = host_name.split(".")

        subdomain = None
        if len(parts) >= 3:
            subdomain = parts[0]

        skip = {"app", "www", "api", "admin", "localhost", "127"}

        request.state.org_slug = None
        request.state.org_id = None

        if subdomain and subdomain not in skip:
            subdomain_lower = subdomain.lower().strip()
            redis_key = f"subdomain:{subdomain_lower}"
            cached_org_id = None

            try:
                redis = await get_redis_pool()
                cached_org_id = await redis.get(redis_key)
            except Exception as e:
                logger.error(f"Redis lookup failed in TenantMiddleware: {e}")

            if cached_org_id:
                request.state.org_slug = subdomain_lower
                request.state.org_id = UUID(cached_org_id.decode() if isinstance(cached_org_id, bytes) else cached_org_id)
            else:
                async with get_db_context() as db:
                    stmt = select(Organization).where(
                        Organization.slug == subdomain_lower,
                        Organization.is_active == True,
                    )
                    res = await db.execute(stmt)
                    org = res.scalar_one_or_none()

                    if org:
                        request.state.org_slug = subdomain_lower
                        request.state.org_id = org.id

                        try:
                            redis = await get_redis_pool()
                            await redis.setex(redis_key, 3600, str(org.id))
                        except Exception as e:
                            logger.error(f"Failed to cache subdomain in Redis: {e}")

        # Resolve user plan for rate limiting
        request.state.plan = "free"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
                if user_id:
                    redis = await get_redis_pool()
                    cache_key = f"user_plan:{user_id}"
                    cached_plan = await redis.get(cache_key)
                    if cached_plan:
                        request.state.plan = cached_plan.decode() if isinstance(cached_plan, bytes) else cached_plan
                    else:
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
                                    request.state.plan = plan
                                    await redis.setex(cache_key, 600, plan)
            except Exception as e:
                logger.error(f"Failed to resolve user plan in TenantMiddleware: {e}")

        return await call_next(request)
