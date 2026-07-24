import re

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.user import Gender

PHONE_REGEX = re.compile(r"^01[0-9]-\d{3,4}-\d{4}$")


def validate_phone_number(phone_number: str) -> str:
    if not PHONE_REGEX.match(phone_number):
        raise ValueError("연락처는 010-1234-5678 형식이어야 합니다.")
    return phone_number


# ---------- Requests ----------

class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="환자 이름")
    age: int = Field(..., ge=0, le=150, description="환자 나이")
    gender: Gender = Field(..., description="성별")
    phone_number: str = Field(..., description="연락처")

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, v: str) -> str:
        return validate_phone_number(v)


class PatientUpdateRequest(BaseModel):
    """REQ-PTNT-004: 이름/연락처만 부분 수정 가능"""
    name: str | None = Field(None, min_length=1, max_length=50, description="환자 이름")
    phone_number: str | None = Field(None, description="연락처")

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return validate_phone_number(v)

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "PatientUpdateRequest":
        if self.name is None and self.phone_number is None:
            raise ValueError("수정할 값을 최소 1개 이상 입력해야 합니다.")
        return self


# ---------- Responses ----------

class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: Gender
    phone_number: str

    model_config = {"from_attributes": True}

