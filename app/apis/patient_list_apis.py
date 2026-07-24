from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.patient import Patient
from app.models.user import Gender, User
from app.schemas.list_responses import PatientListItem

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.get("", response_model=list[PatientListItem])
async def get_patients(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    name: Annotated[str | None, Query(min_length=1)] = None,
    gender: Annotated[Gender | None, Query()] = None,
    min_age: Annotated[int | None, Query(ge=0)] = None,
    max_age: Annotated[int | None, Query(ge=0)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Patient]:
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_age는 max_age보다 클 수 없습니다.",
        )

    query = select(Patient).where(Patient.is_deleted.is_(False))
    if name:
        query = query.where(Patient.name.contains(name))
    if gender:
        query = query.where(Patient.gender == gender)
    if min_age is not None:
        query = query.where(Patient.age >= min_age)
    if max_age is not None:
        query = query.where(Patient.age <= max_age)

    result = await db.execute(
        query.order_by(Patient.id.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all())
