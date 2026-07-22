from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.repositories import medical_record_query_repository


async def get_patient_medical_records(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecord]:
    patient = (
        await medical_record_query_repository.get_patient_by_id(
            db=db,
            patient_id=patient_id,
        )
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )

    return (
        await medical_record_query_repository
        .get_medical_records_by_patient_id(
            db=db,
            patient_id=patient_id,
        )
    )


async def get_medical_record_detail(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord:
    medical_record = (
        await medical_record_query_repository
        .get_medical_record_by_id(
            db=db,
            record_id=record_id,
        )
    )

    if medical_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    return medical_record