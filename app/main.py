from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.admin import setup_admin
from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import check_db_connection, engine
from app.core.exceptions import AppError, ErrorResponse
from app.core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TenantMiddleware,
)
from app.core.rate_limit import limiter
from app.core.redis import check_redis_connection, close_redis_pool
from app.dashboard.routes import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = await check_db_connection()
    if not db_ok:
        raise RuntimeError("Database connection failed on startup.")

    redis_ok = await check_redis_connection()
    if not redis_ok:
        raise RuntimeError("Redis connection failed on startup.")

    print(f"Vorgo started [{settings.ENVIRONMENT}]")
    yield

    await engine.dispose()
    await close_redis_pool()
    print("Vorgo shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Production-ready FastAPI SaaS Boilerplate. Python-only. No React required.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)
app.state.limiter = limiter

setup_admin(app)

# Middleware order matters - last added is outermost.
# RequestIDMiddleware must be inner so request_id is available in all handlers.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error="RATE_LIMITED",
            message="Too many requests. Slow down.",
            details={},
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    details = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details[field] = error["msg"]
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Input validation failed.",
            details=details,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")

    # Handle redirects for browser-facing page requests
    if 300 <= exc.status_code < 400 and exc.headers and "Location" in exc.headers:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(
            url=exc.headers["Location"], status_code=exc.status_code
        )

    error_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMITED",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_map.get(exc.status_code, "HTTP_ERROR"),
            message=str(exc.detail),
            details={},
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            details={},
            request_id=request_id,
        ).model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")
app.include_router(dashboard_router)
