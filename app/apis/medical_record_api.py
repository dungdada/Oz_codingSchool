from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import Department, User, UserRole
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.schemas.medical_record import MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/api/v1/medical-records", tags=["medical-records"])

BASE_DIR = Path(__file__).resolve().parents[2]
XRAY_UPLOAD_DIR = BASE_DIR / "uploads" / "xray"


def require_staff_role(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    is_medical_staff = (
        current_user.role == UserRole.STAFF
        and current_user.department == Department.MEDICAL_TEAM
    )
    if current_user.role != UserRole.ADMIN and not is_medical_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="의료인 권한이 필요합니다.",
        )
    return current_user


@router.post(
    "",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record(
    patient_id: Annotated[int, Form()],
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptoms: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> MedicalRecordResponse:
    repository = MedicalRecordRepository(db)
    service = MedicalRecordService(repository, XRAY_UPLOAD_DIR)
    record = await service.create_medical_record(
        patient_id=patient_id,
        created_by=current_user.id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_image=xray_image,
    )
    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        xray_image_url=record.xray_image_url,
        created_at=record.created_at,
    )
