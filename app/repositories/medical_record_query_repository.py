from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.patient import Patient


async def get_patient_by_id(
    db: AsyncSession,
    patient_id: int,
) -> Patient | None:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
        )
    )

    return result.scalar_one_or_none()


async def get_medical_records_by_patient_id(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecord]:
    result = await db.execute(
        select(MedicalRecord)
        .where(
            MedicalRecord.patient_id == patient_id,
        )
        .order_by(
            MedicalRecord.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_medical_record_by_id(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord | None:
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
        )
    )

    return result.scalar_one_or_none()