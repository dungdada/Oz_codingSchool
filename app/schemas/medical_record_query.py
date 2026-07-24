from datetime import datetime

from pydantic import BaseModel, field_validator


class MedicalRecordListResponse(BaseModel):
    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    @field_validator("symptoms")
    @classmethod
    def truncate_symptoms(cls, value: str) -> str:
        if len(value) > 100:
            return value[:100] + "…"

        return value

    model_config = {
        "from_attributes": True,
    }


class MedicalRecordDetailResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_image_url: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }