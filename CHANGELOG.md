# Changelog

All notable changes to Vorgo will be documented here.

Format: [Semantic Versioning](https://semver.org/)

---

## [0.4.0] - 2026-06-14

### Added
- **Multi-Gateway Billing Layer**
  - Unified `BillingService` factory pattern.
  - Implementations for **Stripe**, **Lemon Squeezy** (webhook verification), **PayPal** (subscriptions API), and **Payoneer** (simulated hosted checkout).
  - Schema migration for unified organization billing fields.
- **Dashboard UI (Tailwind + HTMX + Jinja2)**
  - Responsive layout shell with sidebar navigation.
  - Page views: Overview, Profile Settings, Team Settings, Billing Plans.
  - **Chart.js integration**: API request analytics line chart and resource quota doughnut chart on Overview dashboard.
- **Markdown Blog & Documentation System**
  - Custom `MarkdownService` for parsing YAML frontmatter and Markdown content into styled HTML.
  - Subdomain / Path-based routers for `/docs` and `/blog`.
  - Welcome blog and getting-started documentation pages.

### Fixed
- **Authentication & Hashing Mismatch**
  - Integrated `passlib` context in `fastapi-users` with the application's unified `pwd_context` supporting both `bcrypt` and `argon2` schemes.
  - Resolved nesting class `NameError: name 'password' is not defined` scope bugs in login POST endpoint using `SimpleNamespace`.
  - Added root path `/` redirection handling (routes logged-in users to `/dashboard` and guest users to `/login`).

## [0.3.0] - 2026-06-12

### Added
- **Tenant Invitation System**
  - Schema, model, endpoints (`POST /invite`, `GET /token/{token}`, `POST /accept`, `DELETE /{id}`)
  - Invitation verification, acceptance flow, and role assignments
- **Dynamic Rate Limiting**
  - Integration with `slowapi` and Redis backend
  - Sync-safe `dynamic_rate_limit` wrapper with stack inspection for request retrieval
  - Pre-fetching organization plan subscription tiers in `TenantMiddleware`

### Fixed
- **PostgreSQL Enum Type Mapping**
  - Updated Alembic migrations (`create_core_models.py`, `create_invitations.py`) to map enums using `postgresql.ENUM` with `create_type=False` to handle existing schemas.
  - Added `values_callable=lambda obj: [e.value for e in obj]` to SQLAlchemy `Enum` models to prevent case mismatch between Python names and database values.
- **Database Migrations Event Loop Bug**
  - Fixed sync-async event loop isolation in `setup_db.py` to prevent nested loop exceptions.
- **Pytest Event Loop and DB Isolation**
  - Resolved `attached to a different loop` exceptions in `pytest-asyncio` by adding a session-scoped `event_loop` fixture and a pytest hook to align test loop scopes.
  - Added `clean_database_and_redis` autouse fixture to wipe out DB tables and Redis between tests, ensuring proper test isolation and preventing cache/data leaks.
  - Fixed invitation tests to retrieve tokens directly from the database instead of expecting them in `InvitationResponse`.
  - Fixed direct SMTP email test by patching `EMAIL_FROM` to match config expectations.
- **Email Rendering**
  - Fixed Jinja welcome email template to correctly render `user_name`.

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
