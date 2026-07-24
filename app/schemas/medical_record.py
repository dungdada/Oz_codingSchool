from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    chart_number: str
    symptom: str
    xray_image_url: str
    created_at: datetime


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medical_record_id: int
    is_pneumonia: bool
    confidence: float
    ai_model: str
    created_at: datetime
