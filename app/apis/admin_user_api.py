from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_admin_user
from app.core.db.databases import async_get_db
from app.schemas.admin_user import (
    AdminUserRoleUpdateRequest,
    AdminUserRoleUpdateResponse,
)
from app.services import admin_user_service

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


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
