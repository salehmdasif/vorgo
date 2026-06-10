import asyncio
import urllib.parse
import asyncpg

from app.core.config import settings

async def test():
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
        
    parsed = urllib.parse.urlparse(url)
    user = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    host = parsed.hostname
    port = parsed.port or 5432
    
    print(f"DIAGNOSTIC DETAILS:")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"Parsed username: '{user}'")
    print(f"Parsed password: '{password}'")
    print(f"Host: '{host}', Port: {port}")
    
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres"
        )
        print("SUCCESSFULLY CONNECTED!")
        await conn.close()
    except Exception as e:
        print(f"CONNECTION FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
