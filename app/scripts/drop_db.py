import asyncio
import urllib.parse

import asyncpg

from app.core.config import settings


async def main():
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    parsed = urllib.parse.urlparse(url)
    user = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    host = parsed.hostname
    port = parsed.port or 5432
    db_name = parsed.path.lstrip("/")

    print(f"Connecting to 'postgres' to drop '{db_name}'...")
    conn = await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database="postgres",
    )

    # Check if database exists
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )
    if exists:
        # Terminate active connections to the database to allow dropping it
        await conn.execute(
            f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
              AND pid <> pg_backend_pid();
        """
        )
        await conn.execute(f"DROP DATABASE {db_name}")
        print(f"Database '{db_name}' dropped successfully!")
    else:
        print(f"Database '{db_name}' does not exist.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
