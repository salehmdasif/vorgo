from fastapi import APIRouter

from app.core.auth import fastapi_users
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()

# GET    /users/me     → current user profile
# PATCH  /users/me     → profile update (email, password)
# GET    /users/{id}   → superuser only
# PATCH  /users/{id}   → superuser only
# DELETE /users/{id}   → superuser only
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)
