import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.config import settings
from app.models.base import Base

# main DB এর বদলে আলাদা test DB — production data কখনো touch হবে না
# DB name: vorgo_db → vorgo_test_db
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/vorgo_db", "/vorgo_test_db"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # test session শুরুতে সব table তৈরি করো, শেষে drop করো
    # autouse=True — প্রতিটা test file এ manually call করতে হবে না
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    # প্রতিটা test এর শেষে rollback — test isolation ensure করে
    # একটা test এর data অন্য test এ leak করে না
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    # real HTTP request না করে ASGI transport এ সরাসরি app call করে
    # network overhead নেই, test fast
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
