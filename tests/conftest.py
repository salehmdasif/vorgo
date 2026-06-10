import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.config import settings
from app.models.base import Base

# Use a separate test DB instead of the main DB - production data will never be touched
# DB name: vorgo_db -> vorgo_test_db
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/vorgo_db", "/vorgo_test_db"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


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
