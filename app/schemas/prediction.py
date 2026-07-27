from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    ai_model: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="사용할 모델 식별자. 생략 시 서버 기본 모델을 사용합니다.",
    )


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medical_record_id: int
    is_pneumonia: bool
    confidence: float
    heatmap_image_url: str | None
    ai_model: str
    created_at: datetime
    cached: bool


class PredictionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_image_url: str | None
    created_at: datetime
    ai_model: str


class PredictionListResponse(BaseModel):
    medical_record_id: int
    xray_image_url: str
    predictions: list[PredictionListItem]
