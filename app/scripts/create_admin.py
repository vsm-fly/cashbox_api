import argparse
import asyncio
import sys

from sqlalchemy import select

from app.db.session import async_session
from app.models.user import User, UserRole
from app.core.security import hash_password


async def main(email: str, password: str) -> None:
    async with async_session() as session:
        existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing:
            existing.password_hash = hash_password(password)
            existing.role = UserRole.admin
            await session.commit()
            print(f"Updated admin: {email}")
            return

        user = User(email=email, password_hash=hash_password(password), role=UserRole.admin)
        session.add(user)
        await session.commit()
        print(f"Created admin: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    # Fix for Windows: psycopg async doesn't work with ProactorEventLoop
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(args.email, args.password))
