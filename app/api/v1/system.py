import time
from datetime import UTC, datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.redis import check_redis_connection

router = APIRouter(tags=["System"])

_start_time = time.time()


# ── Response models ───────────────────────────────────────────────────────────


class ServiceStatus(BaseModel):
    database: str
    redis: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    services: ServiceStatus


class MetricsResponse(BaseModel):
    uptime_seconds: float
    version: str
    environment: str
    debug: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    responses={503: {"description": "One or more services are down"}},
)
async def health_check():
    """
    Checks DB and Redis.
    Returns 503 if either is down - load balancers and uptime monitors use this.
    Point UptimeRobot / BetterStack here.
    """
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    all_ok = db_ok and redis_ok
    response = HealthResponse(
        status="ok" if all_ok else "degraded",
        timestamp=datetime.now(UTC).isoformat(),
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        services=ServiceStatus(
            database="ok" if db_ok else "error",
            redis="ok" if redis_ok else "error",
        ),
    )
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=response.model_dump(),
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Basic Runtime Metrics",
)
async def metrics():
    """
    Lightweight runtime info - uptime, version, environment.
    Not a replacement for Prometheus/Grafana - just quick visibility.
    """
    return MetricsResponse(
        uptime_seconds=round(time.time() - _start_time, 2),
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
