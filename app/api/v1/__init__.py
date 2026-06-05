from fastapi import APIRouter

from app.api.v1.system import router as system_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

# নতুন router যোগ হলে এখানে import করো
# Commit 6+: orgs_router, invitations_router, billing_router, etc.

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
