# Changelog

All notable changes to Vorgo will be documented here.

Format: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

## [0.2.0] - 2026-06-05

### Added - Phase 1 Complete (Commits 2-8)

**Database Layer**
- `TenantMixin` - org_id FK + index on all tenant-scoped tables
- `get_db_context()` - async context manager for arq tasks and scripts outside request scope
- `alembic/script.py.mako` - migration template
- Model import block in `alembic/env.py` for autogenerate support

**Core Models**
- `Organization` - plan/subscription enums, Stripe IDs, JSONB settings, slug index
- `User` - fastapi-users compatible, org_id FK, UserRole enum, 2FA fields, backup_codes array
- `AuditLog` - TenantMixin, user_id FK, action/resource tracking, JSONB metadata

**Auth System**
- fastapi-users integration - register, login, email verify, password reset
- `UserRead`, `UserCreate`, `UserUpdate` Pydantic schemas
- Aggregated `api_router` replacing individual router imports

**ED25519 JWT + Redis Token Rotation**
- `ED25519JWTStrategy` - fastapi-users strategy subclass using PyJWT + cryptography
- `create_access_token()`, `create_refresh_token()`, `verify_token()`
- Redis refresh token store, rotation, and revocation (`rt:{user_id}:{jti}`)
- `POST /auth/token` - login and receive access + refresh tokens
- `POST /auth/refresh` - rotate refresh token with reuse detection
- `POST /auth/logout-all` - revoke all sessions

**RBAC + TenantService**
- `TenantService` - org_id scoped `get_all`, `get_one`, `get_by`, `create`, `update`, `delete`, `count`
- `AdminTenantService` - no org_id filter, super admin only
- `require_role()`, `require_superuser()`, `require_verified()` FastAPI dependencies
- `get_tenant_service`, `get_admin_tenant_service` dependencies

**Error Handling**
- `RequestValidationError` handler - Pydantic 422 errors formatted as `ErrorResponse`
- `HTTPException` handler - fastapi-users auth failures formatted as `ErrorResponse`
- Account lockout - 5 failed login attempts triggers 15-minute Redis block
- `ACCOUNT_LOCKED`, `RATE_LIMITED` error codes added
- `Errors` class refactored from lambdas to `@staticmethod` methods

**Health Check + Metrics**
- `/health` - Pydantic response model with version and environment fields
- `/metrics` - uptime_seconds, version, environment, debug flag

### Fixed
- All em dashes removed from code comments and docstrings
- ruff import sorting, unused imports cleaned
- black formatting applied across all files
- `N802` added to ruff ignore (intentional uppercase error method names)

## [0.1.0] - 2026-06-05

### Added
- Initial project scaffolding
- FastAPI application setup with lifespan management
- SQLAlchemy 2.0 async engine and session management
- Redis async connection pool
- Pydantic Settings — `.env` based configuration
- Structured error response system (`AppError`, `ErrorResponse`)
- `RequestIDMiddleware` — per-request UUID tracing
- `SecurityHeadersMiddleware` — XSS, CSRF, clickjacking protection
- CORS configuration
- `GET /api/v1/health` — database + redis health check
- ED25519 key pair generator (`make generate-keys`)
- arq worker skeleton
- Docker + docker-compose setup (pgvector/pg16 + redis:7)
- Alembic async migration setup
- pytest + httpx async test setup
- CI/CD GitHub Actions workflow
- Makefile with common commands
- nginx config for wildcard subdomain routing
