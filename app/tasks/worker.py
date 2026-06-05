from arq.connections import RedisSettings

from app.core.config import settings


async def startup(ctx: dict) -> None:
    # runs once per worker process lifetime
    # initialize shared resources here: db pool, http client, etc.
    pass


async def shutdown(ctx: dict) -> None:
    # runs on graceful worker shutdown
    # close whatever was opened in startup
    pass


class WorkerSettings:
    functions = []  # task functions added here in Commit 14

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown

    max_jobs = 10
    job_timeout = 300  # kill job after 5 minutes
