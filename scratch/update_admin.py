import asyncio
from sqlalchemy import select
from app.core.database import get_db_context
from app.models.user import User

async def run():
    async with get_db_context() as db:
        stmt = select(User).where(User.email == 'admin')
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.email = 'admin@vorgo.com'
            await db.commit()
            print("Successfully updated admin to admin@vorgo.com")
        else:
            print("No user with email 'admin' found.")

if __name__ == "__main__":
    asyncio.run(run())
