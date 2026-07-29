from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.redis_client import enqueue_prediction_task, wait_for_prediction_result
from app.models.ai_analysis import AIAnalysis
from app.models.medical_record import MedicalRecord
from app.repositories.prediction_repository import PredictionRepository


@dataclass(frozen=True)
class PredictionResult:
    analysis: AIAnalysis
    cached: bool


class PredictionService:
    """
    AI 추론은 더 이상 이 프로세스 안에서 실행되지 않는다.
    Redis Stream에 작업을 등록하고, AI 워커(별도 컨테이너)가 처리한 결과를
    Redis Pub/Sub으로 받아서 DB에 저장하는 방식으로 동작한다.
    """

    def __init__(
        self,
        repository: PredictionRepository,
        upload_dir: Path,
    ) -> None:
        self.repository = repository
        self.upload_dir = upload_dir

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

        # 동일 (record_id, ai_model) 요청이 동시에 들어와도 작업은 한 번만 큐에 등록된다.
        # 락을 못 얻은 요청은 먼저 등록된 작업과 같은 결과 채널을 구독해 함께 기다린다.
        task_id, _newly_enqueued = await enqueue_prediction_task(
            record_id=record_id,
            ai_model=settings.AI_MODEL_NAME,
            image_path=str(image_path),
            lock_ttl_seconds=int(settings.AI_INFERENCE_TIMEOUT_SECONDS) + 5,
        )

        result = await wait_for_prediction_result(
            task_id,
            timeout_seconds=settings.AI_INFERENCE_TIMEOUT_SECONDS,
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI 예측 처리 시간이 초과되었습니다.",
            )
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI 예측을 실행할 수 없습니다: {result['error']}",
            )

        try:
            analysis = await self.repository.create(
                record_id=record_id,
                created_by=user_id,
                is_pneumonia=result["is_pneumonia"],
                confidence=Decimal(str(result["confidence"])),
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
