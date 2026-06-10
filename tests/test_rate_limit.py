import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_rate_limiting_triggered(async_client: AsyncClient) -> None:
    # Force dynamic rate limit to a very low value for testing
    with patch("app.core.rate_limit.dynamic_rate_limit", return_value="2/minute"):
        # Make first request
        res1 = await async_client.get("/api/v1/test-rate-limit")
        assert res1.status_code == 200

        # Make second request
        res2 = await async_client.get("/api/v1/test-rate-limit")
        assert res2.status_code == 200

        # Make third request - should exceed limit
        res3 = await async_client.get("/api/v1/test-rate-limit")
        assert res3.status_code == 429
        data = res3.json()
        assert data["error"] == "RATE_LIMITED"
        assert "Too many requests" in data["message"]
