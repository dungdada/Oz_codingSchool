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

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media"


def require_staff_or_admin_user(
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
    dependencies=[Depends(require_staff_or_admin_user)],
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


async def _get_active_patient_or_404(patient_id: int, db: AsyncSession) -> Patient:
    patient = await db.scalar(
        select(Patient).where(Patient.id == patient_id, Patient.is_deleted.is_(False))
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 환자를 찾을 수 없습니다.")
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
    """REQ-PTNT-004 환자 정보 수정 (이름/연락처 Partial Update)"""
    patient = await _get_active_patient_or_404(patient_id, db)

    if payload.name is not None:
        patient.name = payload.name
    if payload.phone_number is not None:
        patient.phone_number = payload.phone_number

    await db.commit()
    await db.refresh(patient)

    return patient


def _delete_xray_file_best_effort(xray_image_url: str) -> None:
    """
    진료기록에 첨부된 X-Ray 이미지 파일을 best-effort로 삭제한다.
    경로 형식이 예상과 다르거나 파일이 없어도 API 자체는 실패시키지 않는다.
    """
    try:
        relative = xray_image_url.removeprefix("/media/").removeprefix("media/")
        file_path = MEDIA_DIR / relative
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception:
        # 파일 삭제 실패는 API 전체 실패로 이어지지 않도록 무시한다.
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
    """
    REQ-PTNT-005 환자 정보 영구 삭제
    연관된 진료기록/AI 분석 결과는 DB FK(ondelete=CASCADE)에 의해 함께 삭제되고,
    로컬에 저장된 X-Ray 이미지 파일도 best-effort로 함께 삭제한다.
    """
    patient = await _get_active_patient_or_404(patient_id, db)

    medical_records = await db.scalars(
        select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)
    )
    for record in medical_records:
        _delete_xray_file_best_effort(record.xray_image_url)

    await db.delete(patient)
    await db.commit()
