import uuid

from fastapi_users import schemas
from pydantic import ConfigDict

from app.models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    """
    User data returned in API responses.
    hashed_password and totp_secret are never exposed.
    """

    org_id: uuid.UUID | None = None
    role: UserRole = UserRole.USER
    totp_enabled: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    """Registration payload: email + password."""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Profile update — password is optional."""

    pass
