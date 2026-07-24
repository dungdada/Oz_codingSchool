from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import my_page_repository


async def get_my_profile(
    db: AsyncSession,
    current_user: User,
) -> User:
    user = await my_page_repository.get_user_by_id(
        db=db,
        user_id=current_user.id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user
