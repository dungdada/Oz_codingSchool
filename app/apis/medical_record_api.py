from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.db.databases import async_get_db
from app.ml import predict_pneumonia
from app.models.ai_analysis import AIAnalysis
from app.models.medical_record import MedicalRecord
from app.models.user import User, UserRole
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.schemas.medical_record import AIAnalysisResponse, MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService

router = APIRouter(prefix="/api/v1/medical-records", tags=["medical-records"])

BASE_DIR = Path(__file__).resolve().parents[2]
XRAY_UPLOAD_DIR = BASE_DIR / "uploads" / "xray"


def require_staff_role(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role not in (UserRole.STAFF, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="의료인 권한이 필요합니다.",
        )
    return current_user


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


@router.post(
    "/{record_id}/analysis",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_medical_record(
    record_id: int,
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> AIAnalysis:
    record = await db.scalar(select(MedicalRecord).where(MedicalRecord.id == record_id))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    image_path = XRAY_UPLOAD_DIR / Path(record.xray_image_url).name
    if not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X-ray 이미지 파일을 찾을 수 없습니다.",
        )

    try:
        prediction = await run_in_threadpool(predict_pneumonia, image_path)
    except (RuntimeError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI 분석을 실행할 수 없습니다: {exc}",
        ) from exc

    analysis = AIAnalysis(
        medical_record_id=record.id,
        created_by=current_user.id,
        is_pneumonia=prediction.is_pneumonia,
        confidence=prediction.confidence,
        ai_model=settings.AI_MODEL_NAME,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
