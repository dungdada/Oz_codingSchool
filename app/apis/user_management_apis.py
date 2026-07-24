from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.user_management import UserProfileUpdateRequest
from app.services import user_management_service


router = APIRouter(
    prefix="/api/v1/users",
    tags=["user-management"],
)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="회원정보 수정",
    description=(
        "로그인한 사용자가 본인의 부서와 "
        "휴대폰 번호를 부분 수정합니다."
    ),
)
async def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> User:
    return await user_management_service.update_my_profile(
        db=db,
        user=current_user,
        request=request,
    )
