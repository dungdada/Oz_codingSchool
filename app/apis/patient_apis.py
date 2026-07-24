from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreateRequest, PatientResponse, PatientUpdateRequest

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])
BASE_DIR = Path(__file__).resolve().parents[2]


def require_staff_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """REQ-PTNT-001: 환자 등록은 사내 의료인(STAFF) 이상만 가능하다."""
    if current_user.role not in (UserRole.STAFF, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="환자 등록 권한이 없습니다.")
    return current_user


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
    dependencies=[Depends(get_current_user)],
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


async def _get_active_patient_or_404(
    patient_id: int,
    db: AsyncSession,
) -> Patient:
    patient = await db.scalar(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 환자를 찾을 수 없습니다.",
        )
    return patient


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_patient(
    patient_id: int,
    payload: PatientUpdateRequest,
    db: AsyncSession = Depends(async_get_db),
) -> Patient:
    patient = await _get_active_patient_or_404(patient_id, db)
    if payload.name is not None:
        patient.name = payload.name
    if payload.phone_number is not None:
        patient.phone_number = payload.phone_number
    await db.commit()
    await db.refresh(patient)
    return patient


def _delete_xray_file_best_effort(xray_image_url: str) -> None:
    file_path = (BASE_DIR / xray_image_url.lstrip("/")).resolve()
    if not file_path.is_relative_to(BASE_DIR.resolve()):
        return
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
) -> None:
    patient = await _get_active_patient_or_404(patient_id, db)
    medical_records = await db.scalars(
        select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
    )
    for record in medical_records:
        _delete_xray_file_best_effort(record.xray_image_url)
    await db.delete(patient)
    await db.commit()
