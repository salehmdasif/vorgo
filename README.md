# Vorgo - FastAPI SaaS Boilerplate

> **Stop assembling. Start building.**

Production-ready FastAPI SaaS boilerplate. Python-only stack. No React required.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)

---

## Why Vorgo

| | Tiangolo Template | SaaS Pegasus | **Vorgo** |
|---|---|---|---|
| Price | Free | $249+ | Free (MIT) |
| Framework | FastAPI | Django | FastAPI |
| React required | Yes | Yes | **No (Optional)** |
| Frontend Flexibility | React Only | Limited | **Any (Next.js/HTMX/Vanilla)** |
| Admin Panel | No | Yes | **Yes** |
| Multi-tenancy | No | Yes | **Yes** |
| Stripe Billing | No | Yes | **Yes** |
| AI Integration | No | No | **Yes** |
| 2FA | No | No | **Yes** |

## Quick Start (With Docker)

```bash
git clone https://github.com/ravelweb/vorgo.git
cd vorgo
pip install -r requirements.txt
cp .env.example .env
make generate-keys     # Generate ED25519 key pair
make docker-up         # Start PostgreSQL + Redis
make migrate           # Run database migrations
make run               # Start the application
```

Open: http://localhost:8000/docs

## Local Setup (Without Docker)

If you prefer to run the services natively on your host machine:

1. **Install PostgreSQL & Redis**:
   - Ensure PostgreSQL is running (default port `5432`).
   - Ensure Redis is running (default port `6379`).
2. **Configure Environment**:
   - Copy `.env.example` to `.env`.
   - Update `DATABASE_URL` and `REDIS_URL` in `.env` with your local credentials.
   - Run `make generate-keys` to generate secure ED25519 token signing keys.
3. **Initialize Databases**:
   - Create the development database (`vorgo_db`) and test database (`vorgo_test_db`) manually or use the helper script:
     ```bash
     python -m app.scripts.create_test_db
     ```
   - Apply migrations and seed the default superuser (`admin`/`admin123`):
     ```bash
     python -m app.scripts.setup_db
     ```
4. **Run Server & Worker**:
   - Start the development server:
     ```bash
     make run
     ```
   - Start the arq task worker:
     ```bash
     make run-worker
     ```

## Testing

Ensure your databases and Redis are running locally. The test suite automatically isolates itself on `vorgo_test_db` and flushes test cache keys.

```bash
make test
```

## Stack

```
FastAPI          → Async web framework
SQLAlchemy 2.0   → Async ORM
Alembic          → Database migrations
Pydantic v2      → Validation + Settings
PostgreSQL       → Primary database (pgvector included)
Redis            → Cache + Sessions + Job queue
arq              → Async background jobs
fastapi-users    → Auth system
PyJWT + crypto   → ED25519 JWT
SQLAdmin         → Admin panel
Stripe, Lemon Squeezy, PayPal, Payoneer → Unified multi-gateway billing
HTMX + Jinja2 + Tailwind + Chart.js     → Interactive server-side dashboard UI (React-free)
```

## Features

- **Auth:** Email/password, OAuth2, 2FA (TOTP), ED25519 JWT, refresh token rotation
- **Multi-tenancy:** Shared schema with TenantService isolation, subdomain routing
- **Billing:** Multi-gateway (Stripe, Lemon Squeezy, PayPal, Payoneer) checkout, webhooks, subscription management, trial logic
- **Dashboard UI:** Jinja2 + HTMX + Tailwind responsive views with Chart.js analytics visualizations
- **Blog & Docs:** Markdown-powered documentation and blog system with YAML frontmatter parsing
- **Admin:** SQLAdmin panel — users, orgs, subscriptions, audit logs
- **AI:** LLM wrapper, token tracking, plan gating, RAG/pgvector
- **Background jobs:** arq (async-native, no Celery friction)
- **Security:** Rate limiting, audit log, account lockout, 2FA, ED25519 JWT
- **DX:** Docker, Makefile, pytest, CI/CD GitHub Actions

## Commands

```bash
make run            # Development server
make run-worker     # arq background worker
make migrate        # Run migrations
make generate-keys  # ED25519 key pair generate
make seed           # Demo data
make test           # Run tests
make lint           # Lint check
make format         # Auto-format
make docker-up      # Start services
```

## Production Checklist

Before launching your SaaS to production, complete the following checklist:

1. **Security & Secrets**:
   - Change `SECRET_KEY` in `.env` to a long, cryptographically secure random string.
   - Run `make generate-keys` to generate new, secure ED25519 token signing keys for production.
   - Do not commit `.env` or any secret credentials to your repository.
2. **Database & Services**:
   - Update `DATABASE_URL` and `REDIS_URL` to point to your production instances.
   - Set `DEBUG=false` in `.env`.
   - Update the default superuser credentials (seeded via `setup_db` as `admin`/`admin123`).
3. **Billing Integration**:
   - Replace Stripe keys (`STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`) with production keys.
   - Set up your Stripe webhook endpoint and configure `STRIPE_WEBHOOK_SECRET`.
4. **Email & Storage Services**:
   - Configure actual production SMTP credentials or set up API keys for email delivery (e.g. Resend/SendGrid).
   - Configure AWS S3 or Cloudflare R2 credentials for user file uploads.

## License

MIT - free for personal and commercial use.
