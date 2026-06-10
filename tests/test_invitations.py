import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.hashing import hash_password
from app.core.security.jwt import create_access_token
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User, UserRole


@pytest_asyncio.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    org = Organization(
        name="Test Org",
        slug="test-org",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_org: Organization) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        org_id=test_org.id,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession, test_org: Organization) -> User:
    user = User(
        email="user@test.com",
        hashed_password=hash_password("password123"),
        org_id=test_org.id,
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_invite_member_success(
    async_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
):
    token = create_access_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "new_member@test.com", "role": "user"}

    response = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_member@test.com"
    assert data["role"] == "user"
    assert data["invited_by"] == str(admin_user.id)
    assert data["accepted_at"] is None

    # Verify database state
    stmt = select(Invitation).where(Invitation.email == "new_member@test.com")
    res = await db_session.execute(stmt)
    invitation = res.scalar_one_or_none()
    assert invitation is not None
    assert invitation.org_id == admin_user.org_id


@pytest.mark.asyncio
async def test_invite_member_forbidden_for_regular_user(
    async_client: AsyncClient,
    regular_user: User,
):
    token = create_access_token(str(regular_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "new_member@test.com", "role": "user"}

    response = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_invitation_details(
    async_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
):
    token = create_access_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "invitee@test.com", "role": "user"}

    res = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    invitation_token = res.json()["token"]

    # Retrieve details publicly using token
    details_res = await async_client.get(
        f"/api/v1/invitations/token/{invitation_token}"
    )
    assert details_res.status_code == 200
    details_data = details_res.json()
    assert details_data["email"] == "invitee@test.com"
    assert details_data["org_name"] == "Test Org"
    assert details_data["role"] == "user"


@pytest.mark.asyncio
async def test_accept_invitation_new_user(
    async_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
):
    # Invite first
    token = create_access_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "invited_new@test.com", "role": "user"}
    res = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    invitation_token = res.json()["token"]

    # Accept invitation
    accept_payload = {"token": invitation_token, "password": "newpassword123"}
    accept_res = await async_client.post(
        "/api/v1/invitations/accept", json=accept_payload
    )
    assert accept_res.status_code == 200
    user_data = accept_res.json()
    assert user_data["email"] == "invited_new@test.com"
    assert user_data["org_id"] == str(admin_user.org_id)
    assert user_data["role"] == "user"

    # Verify DB
    stmt = select(User).where(User.email == "invited_new@test.com")
    res = await db_session.execute(stmt)
    new_user = res.scalar_one_or_none()
    assert new_user is not None
    assert new_user.org_id == admin_user.org_id


@pytest.mark.asyncio
async def test_accept_invitation_existing_user(
    async_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
):
    # Create an existing user belonging to no organization or a different one
    existing = User(
        email="existing_member@test.com",
        hashed_password=hash_password("oldpassword"),
        org_id=None,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    db_session.add(existing)
    await db_session.commit()

    # Invite existing user to admin's organization
    token = create_access_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "existing_member@test.com", "role": "admin"}
    res = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    invitation_token = res.json()["token"]

    # Accept invitation
    accept_payload = {"token": invitation_token}
    accept_res = await async_client.post(
        "/api/v1/invitations/accept", json=accept_payload
    )
    assert accept_res.status_code == 200
    user_data = accept_res.json()
    assert user_data["email"] == "existing_member@test.com"
    assert user_data["org_id"] == str(admin_user.org_id)
    assert user_data["role"] == "admin"
    assert user_data["is_verified"] is True


@pytest.mark.asyncio
async def test_revoke_invitation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
):
    # Invite first
    token = create_access_token(str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"email": "to_revoke@test.com", "role": "user"}
    res = await async_client.post(
        "/api/v1/invitations/invite", json=payload, headers=headers
    )
    invitation_id = res.json()["id"]

    # Revoke invitation
    revoke_res = await async_client.delete(
        f"/api/v1/invitations/{invitation_id}", headers=headers
    )
    assert revoke_res.status_code == 200

    # Verify deleted from DB
    stmt = select(Invitation).where(Invitation.id == invitation_id)
    res = await db_session.execute(stmt)
    invitation = res.scalar_one_or_none()
    assert invitation is None
