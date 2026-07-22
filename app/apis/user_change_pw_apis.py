from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import User
from app.schemas.user_change_pw import UserPasswordUpdateRequest
from app.services import user_change_pw_service


router = APIRouter(
    prefix="/api/v1/users",
    tags=["user-management"],
)


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="비밀번호 변경",
)
async def update_my_password(
    request: UserPasswordUpdateRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> Response:
    await user_change_pw_service.update_my_password(
        db=db,
        user=current_user,
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)