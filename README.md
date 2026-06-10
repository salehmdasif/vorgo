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
| React required | Yes | Yes | **No** |
| Admin Panel | No | Yes | **Yes** |
| Multi-tenancy | No | Yes | **Yes** |
| Stripe Billing | No | Yes | **Yes** |
| AI Integration | No | No | **Yes** |
| 2FA | No | No | **Yes** |

## Quick Start

```bash
git clone https://github.com/ravelweb/vorgo.git
cd vorgo
pip install -r requirements.txt
cp .env.example .env
make generate-keys     # ED25519 key pair তৈরি করে
make docker-up         # PostgreSQL + Redis চালু করে
make migrate           # Database schema তৈরি করে
make run               # App চালু করে
```

Open: http://localhost:8000/docs

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
Stripe           → Billing
HTMX + Jinja2   → Server-side UI (React-free)
```

## Features

- **Auth:** Email/password, OAuth2, 2FA (TOTP), ED25519 JWT, refresh token rotation
- **Multi-tenancy:** Shared schema with TenantService isolation, subdomain routing
- **Billing:** Stripe checkout, webhooks, subscription management, trial logic
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

## License

MIT - free for personal and commercial use.
