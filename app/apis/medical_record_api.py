from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.schemas.medical_record import MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/api/v1/medical-records", tags=["medical-records"])

BASE_DIR = Path(__file__).resolve().parents[2]
XRAY_UPLOAD_DIR = BASE_DIR / "uploads" / "xray"


def require_staff_role(
    x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
) -> None:
    if x_user_role != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="의료인 권한이 필요합니다.",
        )


@router.post(
    "",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff_role)],
)
async def create_medical_record(
    patient_id: Annotated[int, Form()],
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptom: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> MedicalRecordResponse:
    repository = MedicalRecordRepository(db)
    service = MedicalRecordService(repository, XRAY_UPLOAD_DIR)
    record = await service.create_medical_record(
        patient_id=patient_id,
        chart_number=chart_number,
        symptom=symptom,
        xray_image=xray_image,
    )
    return MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        chart_number=record.chart_number,
        symptom=record.symptoms,
        xray_image_url=record.xray_image_url,
        created_at=record.created_at,
    )
