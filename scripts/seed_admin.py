import asyncio
import os

from sqlalchemy import select

from app.core.db.databases import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import Department, Gender, User, UserRole

DEFAULT_EMAIL = "admin@example.com"
DEFAULT_PASSWORD = "Admin1234!"


async def seed_admin() -> None:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("운영 환경에서는 관리자 시드를 실행할 수 없습니다.")

    email = os.getenv("SEED_ADMIN_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("SEED_ADMIN_PASSWORD", DEFAULT_PASSWORD)

    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password=hash_password(password),
                name="개발 관리자",
                department=Department.DEVELOPER,
                gender=Gender.MALE,
                phone_number="010-0000-0000",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
        else:
            user.password = hash_password(password)
            user.role = UserRole.ADMIN
            user.is_active = True

        await db.commit()

    print(f"개발 관리자 계정 준비 완료: {email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
