from datetime import datetime, UTC
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_db_connection
from app.core.redis import check_redis_connection

router = APIRouter(tags=["System"])


@router.get("/health", summary="Health Check")
async def health_check():
    """
    DB আর Redis দুটোই check করে।
    একটাও fail করলে 503 return করে — load balancer এই response এ traffic রুট করবে না।

    uptime monitoring (UptimeRobot, Betterstack) এই endpoint এ point করো।
    """
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    all_ok = db_ok and redis_ok
    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "services": {
                "database": "ok" if db_ok else "error",
                "redis": "ok" if redis_ok else "error",
            },
        },
    )
