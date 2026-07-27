from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.db.databases import async_get_db
from app.models.user import User, UserRole
from app.repositories.prediction_repository import PredictionRepository
from app.core.config import settings
from app.schemas.prediction import (
    PredictionListItem,
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.prediction_service import PredictionService
from worker.model import predict_pneumonia

router = APIRouter(
    prefix="/api/v1/medical-records",
    tags=["predictions"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
XRAY_UPLOAD_DIR = BASE_DIR / "uploads" / "xray"


async def require_prediction_reader(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    if current_user.role not in {
        UserRole.STAFF,
        UserRole.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI 예측 기능을 사용할 권한이 없습니다.",
        )
    return current_user


def get_prediction_service(
    db: AsyncSession,
) -> PredictionService:
    return PredictionService(
        repository=PredictionRepository(db),
        upload_dir=XRAY_UPLOAD_DIR,
        predictor=predict_pneumonia,
    )


async def run_prediction(
    *,
    record_id: int,
    current_user: User,
    db: AsyncSession,
    request: PredictionRequest | None = None,
    normalized_confidence: bool = False,
) -> PredictionResponse:
    if (
        request is not None
        and request.ai_model is not None
        and request.ai_model != settings.AI_MODEL_NAME
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="지원하지 않는 AI 모델입니다.",
        )
    result = await get_prediction_service(db).predict(
        record_id=record_id,
        user_id=current_user.id,
    )
    analysis = result.analysis
    return PredictionResponse(
        id=analysis.id,
        medical_record_id=analysis.medical_record_id,
        is_pneumonia=analysis.is_pneumonia,
        confidence=(
            float(analysis.confidence) / 100
            if normalized_confidence
            else float(analysis.confidence)
        ),
        heatmap_image_url=analysis.heatmap_image_url,
        ai_model=analysis.ai_model,
        created_at=analysis.created_at,
        cached=result.cached,
    )


@router.post(
    "/{record_id}/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 폐렴 예측",
)
async def predict_medical_record(
    record_id: int,
    current_user: Annotated[
        User,
        Depends(require_prediction_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
    request: PredictionRequest | None = None,
) -> PredictionResponse:
    return await run_prediction(
        record_id=record_id,
        current_user=current_user,
        db=db,
        request=request,
        normalized_confidence=True,
    )


@router.get(
    "/{record_id}/predictions",
    response_model=PredictionListResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 폐렴 예측 결과 목록 조회",
)
async def get_medical_record_predictions(
    record_id: int,
    current_user: Annotated[
        User,
        Depends(require_prediction_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> PredictionListResponse:
    record, analyses = await get_prediction_service(db).list_predictions(
        record_id
    )
    return PredictionListResponse(
        medical_record_id=record.id,
        xray_image_url=record.xray_image_url,
        predictions=[
            PredictionListItem(
                id=analysis.id,
                is_pneumonia=analysis.is_pneumonia,
                confidence=float(analysis.confidence) / 100,
                heatmap_image_url=analysis.heatmap_image_url,
                created_at=analysis.created_at,
                ai_model=analysis.ai_model,
            )
            for analysis in analyses
        ],
    )


@router.post(
    "/{record_id}/predict",
    response_model=PredictionResponse,
    include_in_schema=False,
)
@router.post(
    "/{record_id}/analysis",
    response_model=PredictionResponse,
    include_in_schema=False,
)
async def predict_medical_record_legacy(
    record_id: int,
    current_user: Annotated[
        User,
        Depends(require_prediction_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> PredictionResponse:
    return await run_prediction(
        record_id=record_id,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/{record_id}/analyses",
    response_model=list[PredictionListItem],
    include_in_schema=False,
)
async def get_medical_record_predictions_legacy(
    record_id: int,
    _current_user: Annotated[
        User,
        Depends(require_prediction_reader),
    ],
    db: Annotated[
        AsyncSession,
        Depends(async_get_db),
    ],
) -> list[PredictionListItem]:
    _, analyses = await get_prediction_service(db).list_predictions(record_id)
    return [
        PredictionListItem.model_validate(analysis)
        for analysis in analyses
    ]
