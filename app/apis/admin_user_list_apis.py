from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_admin_user
from app.core.db.databases import async_get_db
from app.models.user import Department, User
from app.schemas.list_responses import AdminUserListResponse

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


@router.get("", response_model=AdminUserListResponse)
async def get_admin_users(
    _: Annotated[User, Depends(require_admin_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    keyword: Annotated[str | None, Query(min_length=1)] = None,
    department: Annotated[Department | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> AdminUserListResponse:
    filters = []
    if keyword:
        filters.append(
            or_(
                User.name.contains(keyword),
                User.email.contains(keyword),
            )
        )
    if department:
        filters.append(User.department == department)

    total = await db.scalar(select(func.count(User.id)).where(*filters))
    result = await db.execute(
        select(User)
        .where(*filters)
        .order_by(User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    users = list(result.scalars().all())
    return AdminUserListResponse(
        users=users,
        total=total or 0,
        page=page,
        size=size,
    )
