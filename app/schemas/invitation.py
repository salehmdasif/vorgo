from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER


class InvitationResponse(BaseModel):
    id: UUID
    org_id: UUID
    email: str
    role: UserRole
    invited_by: UUID | None
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationAccept(BaseModel):
    token: str
    password: str | None = None  # Needed if creating a new user account
