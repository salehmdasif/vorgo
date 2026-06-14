from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import Errors
from app.core.rbac import require_role
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
)
from app.schemas.user import UserRead
from app.services.invitation_service import (
    accept_invitation,
    create_invitation,
    get_invitation_by_token,
    revoke_invitation,
)

router = APIRouter(prefix="/invitations", tags=["invitations"])


class InvitationTokenDetails(BaseModel):
    email: str
    org_id: UUID
    org_name: str
    role: UserRole
    expires_at: datetime


@router.post("/invite", response_model=InvitationResponse)
async def invite_member(
    req: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Sends an invitation to a new member.
    Requires organization admin access.
    """
    if not user.org_id:
        raise Errors.FORBIDDEN()

    invitation = await create_invitation(
        db=db,
        org_id=user.org_id,
        email=req.email,
        role=req.role,
        invited_by=user.id,
    )
    return invitation


@router.get("", response_model=list[InvitationResponse])
async def list_invitations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Lists all invitations for the user's organization.
    """
    if not user.org_id:
        raise Errors.FORBIDDEN()

    stmt = select(Invitation).where(Invitation.org_id == user.org_id)
    res = await db.execute(stmt)
    invitations = res.scalars().all()
    return invitations


@router.delete("/{invitation_id}")
async def revoke_member_invitation(
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Revokes a pending invitation.
    """
    if not user.org_id:
        raise Errors.FORBIDDEN()

    await revoke_invitation(db=db, invitation_id=invitation_id, org_id=user.org_id)
    return {"status": "ok", "message": "Invitation revoked successfully."}


@router.get("/token/{token}", response_model=InvitationTokenDetails)
async def get_invitation_details(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates a token and returns details for the signup UI.
    """
    invitation = await get_invitation_by_token(db, token)

    # Check if already accepted
    if invitation.accepted_at is not None:
        raise Errors.VALIDATION_ERROR(
            details={"token": "This invitation has already been accepted."}
        )

    # Get organization name
    stmt = select(Organization.name).where(Organization.id == invitation.org_id)
    res = await db.execute(stmt)
    org_name = res.scalar_one_or_none()

    if not org_name:
        raise Errors.NOT_FOUND("Organization")

    return InvitationTokenDetails(
        email=invitation.email,
        org_id=invitation.org_id,
        org_name=org_name,
        role=invitation.role,
        expires_at=invitation.expires_at,
    )


@router.post("/accept", response_model=UserRead)
async def accept_member_invitation(
    req: InvitationAccept,
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts an invitation, creating or updating user record.
    """
    user = await accept_invitation(db=db, token=req.token, password=req.password)
    return user
