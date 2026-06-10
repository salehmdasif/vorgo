from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security.hashing import hash_password
from app.models.invitation import Invitation
from app.models.user import User, UserRole


async def create_invitation(
    db: AsyncSession,
    org_id: UUID,
    email: str,
    role: UserRole,
    invited_by: UUID,
) -> Invitation:
    """
    Creates a new member invitation for an organization.
    Generates a unique secure token and sets expiry to 7 days.
    """
    email_lower = email.lower().strip()
    
    # 1. Check if user already in this organization
    stmt = select(User).where(User.email == email_lower)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user and existing_user.org_id == org_id:
        raise AppError(
            code="MEMBER_ALREADY_EXISTS",
            message="User is already a member of this organization.",
            status_code=400,
        )

    # 2. Check for pending active invitation
    stmt = select(Invitation).where(
        Invitation.org_id == org_id,
        Invitation.email == email_lower,
        Invitation.accepted_at.is_(None),
        Invitation.expires_at > datetime.now(timezone.utc),
    )
    res = await db.execute(stmt)
    pending = res.scalar_one_or_none()
    if pending:
        raise AppError(
            code="INVITATION_ALREADY_PENDING",
            message="An active invitation is already pending for this email.",
            status_code=400,
        )

    # 3. Create invitation
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invitation = Invitation(
        org_id=org_id,
        email=email_lower,
        token=token,
        role=role,
        invited_by=invited_by,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # TODO: Enqueue email send task via arq in Commit 14
    return invitation


async def get_invitation_by_token(db: AsyncSession, token: str) -> Invitation:
    """
    Looks up an invitation by its token.
    Raises 404 if not found.
    """
    stmt = select(Invitation).where(Invitation.token == token)
    res = await db.execute(stmt)
    invitation = res.scalar_one_or_none()
    if not invitation:
        raise AppError(
            code="INVITATION_NOT_FOUND",
            message="Invitation token is invalid.",
            status_code=404,
        )
    return invitation


async def accept_invitation(
    db: AsyncSession, token: str, password: str | None = None
) -> User:
    """
    Accepts an invitation, creating a new user or updating an existing user's org.
    """
    invitation = await get_invitation_by_token(db, token)

    if invitation.accepted_at is not None:
        raise AppError(
            code="INVITATION_ALREADY_ACCEPTED",
            message="This invitation has already been accepted.",
            status_code=400,
        )

    if invitation.expires_at < datetime.now(timezone.utc):
        raise AppError(
            code="INVITATION_EXPIRED",
            message="This invitation has expired.",
            status_code=400,
        )

    # Check if user already exists
    stmt = select(User).where(User.email == invitation.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if user:
        # User exists, update organization scope and role
        user.org_id = invitation.org_id
        user.role = invitation.role
        user.is_verified = True  # Joining via secure link verifies email
    else:
        # New user, must provide a password
        if not password:
            raise AppError(
                code="PASSWORD_REQUIRED",
                message="Password is required for new users.",
                status_code=400,
            )
        hashed = hash_password(password)
        user = User(
            email=invitation.email,
            hashed_password=hashed,
            org_id=invitation.org_id,
            role=invitation.role,
            is_active=True,
            is_verified=True,
            is_superuser=False,
            totp_enabled=False,
            backup_codes=[],
        )
        db.add(user)

    invitation.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


async def revoke_invitation(db: AsyncSession, invitation_id: UUID, org_id: UUID) -> None:
    """
    Revokes (deletes) a pending invitation for a given organization context.
    """
    stmt = select(Invitation).where(
        Invitation.id == invitation_id, Invitation.org_id == org_id
    )
    res = await db.execute(stmt)
    invitation = res.scalar_one_or_none()
    if not invitation:
        raise AppError(
            code="INVITATION_NOT_FOUND",
            message="Invitation not found in this organization.",
            status_code=404,
        )
    if invitation.accepted_at:
        raise AppError(
            code="INVITATION_ALREADY_ACCEPTED",
            message="Cannot revoke an accepted invitation.",
            status_code=400,
        )
    await db.delete(invitation)
    await db.commit()
