from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def update_user_password(
    db: AsyncSession,
    user: User,
    hashed_password: str,
) -> User:
    user.password = hashed_password

    await db.flush()

    return user