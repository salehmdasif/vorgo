from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    প্রতিটা request এ unique ID inject করে।
    error log এ request_id দিয়ে Sentry বা structlog এ trace করা যায়।
    response header এও পাঠায় — frontend থেকে support ticket এ দেওয়া যাবে।
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id  # error handler এ access করবে
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Browser-level attack vector গুলো বন্ধ করে।

    X-Content-Type-Options  → MIME sniffing বন্ধ
    X-Frame-Options         → clickjacking বন্ধ (iframe embed করা যাবে না)
    X-XSS-Protection        → legacy XSS filter (modern browser এ built-in)
    Referrer-Policy         → cross-origin request এ referer header limit করে
    Permissions-Policy      → camera, mic, location access বন্ধ
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response
