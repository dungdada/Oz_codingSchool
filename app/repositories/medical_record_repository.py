from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.patient import Patient


class MedicalRecordRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_patient(self, patient_id: int) -> Patient | None:
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        patient_id: int,
        chart_number: str,
        symptom: str,
        xray_image_url: str,
    ) -> MedicalRecord:
        record = MedicalRecord(
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptom,
            xray_image_url=xray_image_url,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
