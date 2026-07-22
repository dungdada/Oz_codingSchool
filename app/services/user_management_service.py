from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user_management_repository
from app.schemas.user_management import UserProfileUpdateRequest


async def update_my_profile(
    db: AsyncSession,
    user: User,
    request: UserProfileUpdateRequest,
) -> User:
    update_data = request.model_dump(exclude_unset=True)

    try:
        updated_user = (
            await user_management_repository.update_user_profile(
                db=db,
                user=user,
                update_data=update_data,
            )
        )

        await db.commit()
        await db.refresh(updated_user)

        return updated_user

    except Exception:
        await db.rollback()
        raise