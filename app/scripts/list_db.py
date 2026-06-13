import asyncio
import asyncpg
from app.core.config import settings

async def main():
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    
    # Query types
    types = await conn.fetch("SELECT typname FROM pg_type WHERE typtype = 'e';")
    print("Enums in DB:", [t['typname'] for t in types])
    
    # Query tables
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    print("Tables in DB:", [t['tablename'] for t in tables])
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
