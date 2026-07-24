from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import User
from app.schemas.my_page import MyPageResponse
from app.services import my_page_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=MyPageResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> User:
    return await my_page_service.get_my_profile(db=db, current_user=current_user)
