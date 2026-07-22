from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Department, User, UserRole


async def get_users(
    db: AsyncSession,
    query: str | None = None,
    department: Department | None = None,
) -> list[User]:
    statement = select(User).order_by(User.id)

    if query:
        keyword = f"%{query}%"
        statement = statement.where(User.name.like(keyword) | User.email.like(keyword))

    if department:
        statement = statement.where(User.department == department)

    result = await db.execute(statement)
    return list(result.scalars().all())


async def get_users_by_ids(db: AsyncSession, user_ids: list[int]) -> list[User]:
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return list(result.scalars().all())


async def update_users_role(db: AsyncSession, users: list[User], role: UserRole) -> list[User]:
    for user in users:
        user.role = role

    await db.commit()

    for user in users:
        await db.refresh(user)

    return users
