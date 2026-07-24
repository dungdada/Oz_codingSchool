from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_change_pw_repository
from app.schemas.user_change_pw import UserPasswordUpdateRequest


async def update_my_password(
    db: AsyncSession,
    user: User,
    request: UserPasswordUpdateRequest,
) -> None:
    password_matches = verify_password(
        plain_password=request.current_password,
        hashed_password=user.password,
    )

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다.",
        )

    hashed_password = hash_password(request.new_password)

    try:
        await user_change_pw_repository.update_user_password(
            db=db,
            user=user,
            hashed_password=hashed_password,
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise