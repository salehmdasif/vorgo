import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

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


_mock_limit = None


def dynamic_rate_limit(request: Request = None) -> str:
    """
    Resolves the appropriate rate limit string based on the user's organization plan.
    Uses pre-fetched plan from TenantMiddleware request state.
    """
    if _mock_limit is not None:
        return _mock_limit

    if request is None:
        import inspect

        from starlette.requests import Request as StarletteRequest

        for frame_info in inspect.stack():
            if "request" in frame_info.frame.f_locals:
                obj = frame_info.frame.f_locals["request"]
                if isinstance(obj, StarletteRequest):
                    request = obj
                    break
            if "self" in frame_info.frame.f_locals:
                self_obj = frame_info.frame.f_locals["self"]
                if hasattr(self_obj, "request") and isinstance(
                    getattr(self_obj, "request"), StarletteRequest
                ):
                    request = self_obj.request
                    break

    if not request:
        return "100/hour"

    # Default fallback limit for unauthenticated requests
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return "20/minute"

    plan = getattr(request.state, "plan", "free")
    return RATE_LIMITS.get(plan, "100/hour")
