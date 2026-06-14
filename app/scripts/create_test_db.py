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
    db_name = "vorgo_test_db"

    print(f"Connecting to 'postgres' to create '{db_name}'...")
    conn = await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database="postgres",
    )

    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )
    if not exists:
        await conn.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully!")
    else:
        print(f"Database '{db_name}' already exists.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
