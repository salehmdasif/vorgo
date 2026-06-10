import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")

    # 200 = OK, 503 = degraded (No DB or Redis connection)
    # Both are valid in the test environment if services are not available
    assert response.status_code in [200, 503]

    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
