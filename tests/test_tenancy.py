import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


@pytest.mark.asyncio
async def test_subdomain_resolution_no_subdomain(async_client: AsyncClient) -> None:
    # No subdomain, e.g. localhost or api.yourdomain.com
    response = await async_client.get("/api/v1/test-tenant")
    assert response.status_code == 200
    data = response.json()
    assert data["org_slug"] is None
    assert data["org_id"] is None


@pytest.mark.asyncio
async def test_subdomain_resolution_with_active_org(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Create an active organization
    org = Organization(
        name="Acme Corp",
        slug="acme",
        is_active=True,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    # Make request with Host header specifying the subdomain
    headers = {"Host": "acme.lvh.me"}
    response = await async_client.get("/api/v1/test-tenant", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["org_slug"] == "acme"
    assert data["org_id"] == str(org.id)


@pytest.mark.asyncio
async def test_subdomain_resolution_inactive_org(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Create an inactive organization
    org = Organization(
        name="Inactive Corp",
        slug="inactive",
        is_active=False,
    )
    db_session.add(org)
    await db_session.commit()

    headers = {"Host": "inactive.lvh.me"}
    response = await async_client.get("/api/v1/test-tenant", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["org_slug"] is None
    assert data["org_id"] is None
