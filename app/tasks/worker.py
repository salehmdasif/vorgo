from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.tasks.billing_tasks import trial_expiry_check
from app.tasks.email_tasks import send_email_task


async def startup(ctx: dict) -> None:
    """
    Runs once per worker process lifetime.
    Initialize shared resources here: db pool, http client, etc.
    """
    pass


async def shutdown(ctx: dict) -> None:
    """
    Runs on graceful worker shutdown.
    Close whatever was opened in startup.
    """
    pass


class WorkerSettings:
    functions = [send_email_task]
    cron_jobs = [
        cron(trial_expiry_check, hour=0, minute=0)  # Run daily at midnight
    ]

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown

    max_jobs = 10
    job_timeout = 300  # Kill job after 5 minutes
