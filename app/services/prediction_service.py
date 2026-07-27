import asyncio
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.ml.pneumonia_predictor import PneumoniaPrediction
from app.models.ai_analysis import AIAnalysis
from app.models.medical_record import MedicalRecord
from app.repositories.prediction_repository import PredictionRepository

Predictor = Callable[[Path], PneumoniaPrediction]


@dataclass(frozen=True)
class PredictionResult:
    analysis: AIAnalysis
    cached: bool


class PredictionService:
    def __init__(
        self,
        repository: PredictionRepository,
        upload_dir: Path,
        predictor: Predictor,
    ) -> None:
        self.repository = repository
        self.upload_dir = upload_dir
        self.predictor = predictor

    async def predict(
        self,
        *,
        record_id: int,
        user_id: int,
    ) -> PredictionResult:
        record = await self.repository.get_medical_record(record_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="진료기록을 찾을 수 없습니다.",
            )

        cached = await self.repository.get_by_record_and_model(
            record_id=record_id,
            ai_model=settings.AI_MODEL_NAME,
        )
        if cached is not None:
            return PredictionResult(analysis=cached, cached=True)

        image_path = self.upload_dir / Path(record.xray_image_url).name
        if not image_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="X-ray 이미지 파일을 찾을 수 없습니다.",
            )

        try:
            prediction = await asyncio.wait_for(
                run_in_threadpool(self.predictor, image_path),
                timeout=settings.AI_INFERENCE_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI 예측 처리 시간이 초과되었습니다.",
            ) from exc
        except (RuntimeError, OSError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI 예측을 실행할 수 없습니다: {exc}",
            ) from exc

        try:
            analysis = await self.repository.create(
                record_id=record_id,
                created_by=user_id,
                is_pneumonia=prediction.is_pneumonia,
                confidence=Decimal(str(prediction.confidence)),
                ai_model=settings.AI_MODEL_NAME,
                heatmap_image_url=None,
            )
            await self.repository.db.commit()
            await self.repository.db.refresh(analysis)
            return PredictionResult(analysis=analysis, cached=False)
        except IntegrityError:
            # 동시에 같은 요청이 들어온 경우 Unique 제약조건이 중복 저장을 막는다.
            await self.repository.db.rollback()
            cached = await self.repository.get_by_record_and_model(
                record_id=record_id,
                ai_model=settings.AI_MODEL_NAME,
            )
            if cached is None:
                raise
            return PredictionResult(analysis=cached, cached=True)
        except Exception:
            await self.repository.db.rollback()
            raise

    async def list_predictions(
        self,
        record_id: int,
    ) -> tuple[MedicalRecord, list[AIAnalysis]]:
        record = await self.repository.get_medical_record(record_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="진료기록을 찾을 수 없습니다.",
            )
        return record, await self.repository.list_by_record(record_id)
