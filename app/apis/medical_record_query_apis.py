from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.medical_record import MedicalRecord
from app.models.user import User, UserRole
from app.schemas.medical_record_query import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)
from app.services import medical_record_query_service


router = APIRouter(
    prefix="/api/v1",
    tags=["medical-records"],
)


async def require_medical_record_reader(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    allowed_roles = {
        UserRole.STAFF,
        UserRole.ADMIN,
    }

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="진료기록을 조회할 권한이 없습니다.",
        )

    return current_user


@router.get(
    "/patients/{patient_id}/medical-records",
    response_model=list[MedicalRecordListResponse],
    summary="환자별 진료기록 목록 조회",
)
async def get_patient_medical_records(
    patient_id: int,
    current_user: Annotated[
        User,
        Depends(require_medical_record_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> list[MedicalRecord]:
    return (
        await medical_record_query_service
        .get_patient_medical_records(
            db=db,
            patient_id=patient_id,
        )
    )


@router.get(
    "/medical-records/{record_id}",
    response_model=MedicalRecordDetailResponse,
    summary="진료기록 상세 조회",
)
async def get_medical_record_detail(
    record_id: int,
    current_user: Annotated[
        User,
        Depends(require_medical_record_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> MedicalRecord:
    return (
        await medical_record_query_service
        .get_medical_record_detail(
            db=db,
            record_id=record_id,
        )
    )
