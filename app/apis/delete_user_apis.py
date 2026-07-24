from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import User
from app.services import delete_user_service


router = APIRouter(
    prefix="/api/v1/users",
    tags=["user-management"],
)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원탈퇴",
    description=(
        "로그인한 회원과 해당 회원에 관련된 "
        "데이터를 데이터베이스에서 즉시 삭제합니다."
    ),
)
async def delete_my_account(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> Response:
    await delete_user_service.delete_my_account(
        db=db,
        user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
