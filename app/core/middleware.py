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

        return await call_next(request)
