from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import text
from app.core.config import settings


# pool_pre_ping=True — stale connection কে automatically drop করে নতুন নেয়
# pool_size=20, max_overflow=10 — total max 30 concurrent connections
# production এ এই numbers PostgreSQL এর max_connections এর সাথে মিলিয়ে tune করো
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=settings.DEBUG,  # DEBUG=True হলে SQL query log এ দেখা যাবে
)

# expire_on_commit=False — commit এর পরেও object access করা যাবে
# এটা না থাকলে commit এর পরে attribute access এ lazy load error আসে
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # FastAPI Depends() এ use করো — request শেষে automatically close হবে
    # success হলে commit, exception হলে rollback — caller কে ভাবতে হবে না
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    arq background task, seeder script, বা CLI command এ use করো।
    FastAPI request scope এর বাইরে DB session দরকার হলে এটা।

    Usage (arq task):
        async def my_task(ctx):
            async with get_db_context() as db:
                result = await db.execute(select(User))

    get_db() এর সাথে পার্থক্য:
    - get_db() → FastAPI Depends() এ, request lifecycle এ bound
    - get_db_context() → যেকোনো async context এ, manually manage করা
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    # startup health check এ use হয়
    # False return করলে app startup এই crash করবে
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
