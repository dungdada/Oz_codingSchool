from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import delete_user_repository


async def delete_my_account(
    db: AsyncSession,
    user: User,
) -> None:
    try:
        await delete_user_repository.delete_user_and_related_data(
            db=db,
            user=user,
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise