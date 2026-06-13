import asyncio
from sqlalchemy import select
from app.core.database import get_db_context
from app.models.user import User
from app.core.security.hashing import verify_password

async def run():
    async with get_db_context() as db:
        stmt = select(User).where(User.email == 'admin@vorgo.com')
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            print(f"User found: {user.email}")
            print(f"Hashed password in DB: {user.hashed_password}")
            
            # Verify password
            is_valid = verify_password("admin123", user.hashed_password)
            print(f"Is password valid? {is_valid}")
        else:
            print("User admin@vorgo.com not found in DB!")

if __name__ == "__main__":
    asyncio.run(run())
