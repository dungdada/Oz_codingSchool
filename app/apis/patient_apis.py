from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.models.patient import Patient
from app.models.user import UserRole
from app.schemas.patient import PatientCreateRequest, PatientResponse

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def require_authenticated(
    authorization: Annotated[str | None, Header()] = None,
    x_user_role: Annotated[UserRole | None, Header(alias="X-User-Role")] = None,
) -> UserRole:
    """
    로그인 여부만 확인한다.
    TODO: 로그인(JWT) API가 merge되면 Authorization 헤더의 토큰을 실제로 검증하도록 교체 필요.
    """
    if not authorization or x_user_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다.")
    return x_user_role


def require_staff_or_admin(role: Annotated[UserRole, Depends(require_authenticated)]) -> UserRole:
    """REQ-PTNT-001: 환자 등록은 사내 의료인(STAFF) 이상만 가능하다."""
    if role not in (UserRole.STAFF, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자 등록 권한이 없습니다.")
    return role


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff_or_admin)],
)
async def create_patient(
    payload: PatientCreateRequest,
    db: AsyncSession = Depends(async_get_db),
) -> Patient:
    """REQ-PTNT-001 환자 정보 등록"""
    new_patient = Patient(
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        phone_number=payload.phone_number,
    )
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    return new_patient


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    dependencies=[Depends(require_authenticated)],
)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
) -> Patient:
    """REQ-PTNT-003 환자 정보 상세 조회"""
    patient = await db.scalar(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 환자를 찾을 수 없습니다.")

    return patient
