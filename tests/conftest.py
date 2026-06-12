import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

# Use a separate test DB instead of the main DB - production data will never be touched
# DB name: vorgo_db -> vorgo_test_db
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/vorgo_db", "/vorgo_test_db"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

# Override the application's DB engine and sessionmaker so the app uses the test DB
import app.core.database
app.core.database.engine = test_engine
app.core.database.AsyncSessionLocal = TestSessionLocal

from app.main import app
from app.models.base import Base


def pytest_collection_modifyitems(items):
    for item in items:
        for marker in item.iter_markers(name="asyncio"):
            if "loop_scope" not in marker.kwargs:
                marker.kwargs["loop_scope"] = "session"


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_database_and_redis():
    # Clean Redis
    try:
        from app.core.redis import get_redis_pool
        redis = await get_redis_pool()
        await redis.flushdb()
    except Exception:
        pass

    # Clean DB
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Create all tables at the start of the test session, drop them at the end
    # autouse=True - no need to call manually in every test file
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    # Rollback at the end of each test - ensures test isolation
    # Data from one test does not leak into other tests
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    # Calls the app directly via ASGI transport instead of making real HTTP requests
    # No network overhead, fast tests
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
