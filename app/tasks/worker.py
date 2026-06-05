from arq.connections import RedisSettings
from app.core.config import settings

# arq use করা হয়েছে Celery এর বদলে কারণ:
# - native async - FastAPI এর async context এর সাথে friction নেই
# - Celery তে async function এ await করতে গেলে আলাদা event loop লাগে
# - same Redis instance use করে যেটা cache আর rate limiting এও আছে


async def startup(ctx: dict) -> None:
    # worker process এর lifetime এ একবার চলে
    # shared resources এখানে initialize করো - db pool, http client, etc.
    # commit 14 এ email_service, db connection যোগ হবে
    pass


async def shutdown(ctx: dict) -> None:
    # worker graceful shutdown এ চলে
    # startup এ যা open করেছো সেটা এখানে close করো
    pass


class WorkerSettings:
    # functions list এ task function গুলো যোগ করো
    # commit 14 এ: [send_email_task, deliver_webhook_task, ...]
    functions = []

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown

    max_jobs = 10       # একই সময়ে maximum এতগুলো job চলবে
    job_timeout = 300   # 5 মিনিটের বেশি চললে kill করবে
