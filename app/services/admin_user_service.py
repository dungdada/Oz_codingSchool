from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Department, User, UserRole
from app.repositories import admin_user_repository
from app.schemas.admin_user import AdminUserRoleUpdateRequest


async def get_admin_users(
    db: AsyncSession,
    query: str | None = None,
    department: Department | None = None,
) -> list[User]:
    return await admin_user_repository.get_users(db, query=query, department=department)


async def update_user_roles(db: AsyncSession, request: AdminUserRoleUpdateRequest) -> list[User]:
    user_ids = list(dict.fromkeys(request.user_ids))
    users = await admin_user_repository.get_users_by_ids(db, user_ids)

    found_user_ids = {user.id for user in users}
    missing_user_ids = [user_id for user_id in user_ids if user_id not in found_user_ids]
    if missing_user_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "존재하지 않는 회원이 포함되어 있습니다.", "user_ids": missing_user_ids},
        )

    return await admin_user_repository.update_users_role(db, users, request.new_role)
