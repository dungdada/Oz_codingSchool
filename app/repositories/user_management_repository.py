from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def update_user_profile(
    db: AsyncSession,
    user: User,
    update_data: dict,
) -> User:
    for field_name, value in update_data.items():
        setattr(user, field_name, value)

    await db.flush()

    return user