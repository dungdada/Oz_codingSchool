from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.models.medical_record import MedicalRecord


class PredictionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_medical_record(
        self,
        record_id: int,
    ) -> MedicalRecord | None:
        return await self.db.get(MedicalRecord, record_id)

    async def get_by_record_and_model(
        self,
        record_id: int,
        ai_model: str,
    ) -> AIAnalysis | None:
        return await self.db.scalar(
            select(AIAnalysis).where(
                AIAnalysis.medical_record_id == record_id,
                AIAnalysis.ai_model == ai_model,
            )
        )

    async def list_by_record(
        self,
        record_id: int,
    ) -> list[AIAnalysis]:
        result = await self.db.scalars(
            select(AIAnalysis)
            .where(AIAnalysis.medical_record_id == record_id)
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id.desc(),
            )
        )
        return list(result.all())

    async def create(
        self,
        *,
        record_id: int,
        created_by: int,
        is_pneumonia: bool,
        confidence: Decimal,
        ai_model: str,
        heatmap_image_url: str | None,
    ) -> AIAnalysis:
        analysis = AIAnalysis(
            medical_record_id=record_id,
            created_by=created_by,
            is_pneumonia=is_pneumonia,
            confidence=confidence,
            ai_model=ai_model,
            heatmap_image_url=heatmap_image_url,
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis
