import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.models.base import Base  # noqa: F401

# -- Model imports -------------------------------------------------------------
# Import new models below.
# Otherwise, 'make migration' autogenerate will not detect the new table.
# Import order does not matter - alembic resolves the dependency graph itself.

# Commit 3 - core models
from app.models.organization import Organization  # noqa: F401
from app.models.user import User                  # noqa: F401
from app.models.audit_log import AuditLog         # noqa: F401

# Commit 5+:
from app.models.feature_flag import FeatureFlag   # noqa: F401
# from app.models.invitation import Invitation      # noqa: F401
# from app.models.api_key import APIKey             # noqa: F401
# from app.models.ai_usage import AIUsage           # noqa: F401
# from app.models.webhook import WebhookEndpoint, WebhookDelivery  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the url in alembic.ini - it needs to be taken from settings
# Hardcoding it could run migrations on the wrong database if the environment changes
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # `alembic upgrade head --sql` - generates SQL without an actual DB connection
    # Useful for dry-runs in CI/CD or DBA review
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # NullPool - connection pool is not needed for migrations
    # Keeping the pool might cause connections to hang after migration
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
