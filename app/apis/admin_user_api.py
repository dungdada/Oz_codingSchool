from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.dependencies import get_current_user
from app.models.user import Department, User, UserRole
from app.schemas.admin_user import (
    AdminUserResponse,
    AdminUserRoleUpdateRequest,
    AdminUserRoleUpdateResponse,
)
from app.services import admin_user_service

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


def require_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return current_user


@router.get(
    "",
    response_model=list[AdminUserResponse],
    dependencies=[Depends(require_admin_user)],
)
async def get_admin_users(
    query: str | None = Query(default=None),
    department: Department | None = Query(default=None),
    db: AsyncSession = Depends(async_get_db),
) -> list[AdminUserResponse]:
    return await admin_user_service.get_admin_users(db, query=query, department=department)


@router.patch(
    "/role",
    response_model=AdminUserRoleUpdateResponse,
    dependencies=[Depends(require_admin_user)],
)
async def update_user_roles(
    request: AdminUserRoleUpdateRequest,
    db: AsyncSession = Depends(async_get_db),
) -> AdminUserRoleUpdateResponse:
    users = await admin_user_service.update_user_roles(db, request)
    return AdminUserRoleUpdateResponse(updated_count=len(users), users=users)
