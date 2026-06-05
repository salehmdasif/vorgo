# Changelog

All notable changes to Vorgo will be documented here.

Format: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

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
