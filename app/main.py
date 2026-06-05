from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError, ErrorResponse
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.core.database import check_db_connection, engine
from app.core.redis import check_redis_connection, close_redis_pool
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────
    # DB বা Redis fail করলে app চলতে দেওয়া ঠিক না
    # misconfigured state এ request নেওয়া শুরু করলে silent error হবে
    db_ok = await check_db_connection()
    if not db_ok:
        raise RuntimeError("Database connection failed on startup.")

    redis_ok = await check_redis_connection()
    if not redis_ok:
        raise RuntimeError("Redis connection failed on startup.")

    print(f"Vorgo started [{settings.ENVIRONMENT}]")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    # graceful shutdown — in-flight request শেষ হওয়ার পর connection close হবে
    await engine.dispose()
    await close_redis_pool()
    print("Vorgo shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Production-ready FastAPI SaaS Boilerplate. Python-only. No React required.",
    # production এ docs বন্ধ রাখো — API structure expose করা ঠিক না
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
# IMPORTANT: order matters — stack এর মতো কাজ করে, last added = outermost
# RequestID আগে add হওয়া দরকার যাতে সব handler এ request_id পাওয়া যায়
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sentry ────────────────────────────────────────────────────────────────────
# SENTRY_DSN .env এ না থাকলে initialize হবে না — dev এ noise নেই
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
    )


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # সব business logic error এখানে আসে
    # request_id না পেলে "unknown" — middleware miss করলে fallback
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # catch-all — unexpected error যেন raw traceback client এ না যায়
    # Sentry এ automatically capture হবে যদি configured থাকে
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


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")
