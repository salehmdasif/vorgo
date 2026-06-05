import uuid
from pydantic import ConfigDict
from fastapi_users import schemas

from app.models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    """
    API response এ যে User data client পাবে।

    BaseUser থেকে আসে: id, email, is_active, is_verified, is_superuser
    hashed_password কখনো expose হয় না — BaseUser এ নেই।
    totp_secret কখনো expose হয় না — intentionally বাদ।
    """

    org_id: uuid.UUID | None = None
    role: UserRole = UserRole.USER
    totp_enabled: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    """
    Registration এ client থেকে নেওয়া হবে: email + password।
    fastapi-users password strength validation করে।
    """

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """
    Profile update — password optional।
    current_password দিতে হবে password change করতে (fastapi-users enforce করে)।
    """

    pass
