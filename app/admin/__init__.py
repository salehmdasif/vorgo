# ── Imports ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from app.admin.auth import AdminAuth
from app.admin.views import AuditLogAdmin, OrganizationAdmin, UserAdmin, FeatureFlagAdmin
from app.core.config import settings
from app.core.database import engine

# ── Admin Panel Registration ──────────────────────────────────────────────────


def setup_admin(app: FastAPI) -> None:
    """
    Bootstraps the SQLAdmin panel on the FastAPI application.
    Registers SessionMiddleware (required by sqladmin for authentication cookies).
    Registers admin models views.
    """
    # Starlette session middleware is required for keeping admin login session state
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend,
        title="Vorgo Admin",
        base_url="/admin",
    )

    admin.add_view(UserAdmin)
    admin.add_view(OrganizationAdmin)
    admin.add_view(AuditLogAdmin)
    admin.add_view(FeatureFlagAdmin)
