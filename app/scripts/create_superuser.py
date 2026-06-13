import asyncio
from sqlalchemy import select

from app.core.database import get_db_context
from app.core.security.hashing import hash_password
from app.models.user import User, UserRole


async def create_admin() -> None:
    email = "admin@vorgo.com"
    password = "admin123"

    print("Connecting to database...")
    async with get_db_context() as db:
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            print(f"User {email} already exists. Promoting to superuser...")
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.role = UserRole.SUPER_ADMIN
            await db.commit()
            print("Successfully promoted!")
            return

        print(f"Creating superuser {email}...")
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


if __name__ == "__main__":
    asyncio.run(create_admin())
