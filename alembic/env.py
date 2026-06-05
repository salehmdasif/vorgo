import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.config import settings
from app.models.base import Base

# নতুন model তৈরি করলে এখানে import করতে হবে
# না করলে autogenerate migration এ নতুন table detect হবে না
# from app.models.user import User
# from app.models.organization import Organization

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# alembic.ini এর url override করছি — settings থেকে নেওয়া দরকার
# hardcode করলে environment আলাদা হলে ভুল DB তে migration চলবে
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # `alembic upgrade head --sql` — actual DB connection ছাড়া SQL generate করে
    # CI/CD এ dry-run বা DBA review এর জন্য useful
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
    # NullPool — migration এ connection pool দরকার নেই
    # pool রাখলে migration শেষে connection hang করতে পারে
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
