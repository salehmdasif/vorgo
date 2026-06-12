import asyncio
import os
from alembic import command
from alembic.config import Config
import asyncpg
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context
from app.core.security.hashing import hash_password
from app.models.user import User, UserRole


async def create_db() -> None:
    import urllib.parse

    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    parsed = urllib.parse.urlparse(url)
    user = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    host = parsed.hostname
    port = parsed.port or 5432
    db_name = parsed.path.lstrip("/")

    print(f"Connecting to system database 'postgres' to check for database '{db_name}'...")
    conn = await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database="postgres",
    )
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
    if not exists:
        print(f"Database '{db_name}' does not exist. Creating it now...")
        await conn.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully!")
    else:
        print(f"Database '{db_name}' already exists.")
    await conn.close()


def run_migrations() -> None:
    print("Running Alembic migrations...")
    original_cwd = os.getcwd()
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    os.chdir(script_dir)
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Migrations successfully applied!")
    finally:
        os.chdir(original_cwd)


async def create_admin() -> None:
    email = "admin"
    password = "admin123"
    print("Creating/checking superuser in database...")
    async with get_db_context() as db:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            print(f"Superuser '{email}' already exists. Re-verifying...")
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.role = UserRole.SUPER_ADMIN
            await db.commit()
            print("Superuser verification updated.")
            return

        hashed = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed,
            org_id=None,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            is_superuser=True,
            totp_enabled=False,
            backup_codes=[],
        )
        db.add(user)
        await db.commit()
        print("Superuser successfully created!")
        print(f"Username: {email}")
        print(f"Password: {password}")


def main() -> None:
    asyncio.run(create_db())
    run_migrations()
    asyncio.run(create_admin())
    print("\nInitialization complete! You can now run the app.")


if __name__ == "__main__":
    main()
