import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import Department, Gender, UserRole

PHONE_REGEX = re.compile(r"^01[0-9]-\d{3,4}-\d{4}$")


def validate_password_rules(password: str) -> str:
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("비밀번호는 영문을 최소 1자 포함해야 합니다.")
    if not re.search(r"[0-9]", password):
        raise ValueError("비밀번호는 숫자를 최소 1자 포함해야 합니다.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=~`\[\]/;']", password):
        raise ValueError("비밀번호는 특수문자를 최소 1자 포함해야 합니다.")
    return password


def validate_phone_number(phone_number: str) -> str:
    if not PHONE_REGEX.match(phone_number):
        raise ValueError("휴대폰 번호는 010-1234-5678 형식이어야 합니다.")
    return phone_number


# ---------- Requests ----------

class UserSignupRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, max_length=64, description="비밀번호")
    name: str = Field(..., min_length=1, max_length=50, description="사용자 이름")
    department: Department = Field(..., description="부서")
    gender: Gender = Field(..., description="성별")
    phone_number: str = Field(..., description="휴대폰 번호")

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_rules(v)

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, v: str) -> str:
        return validate_phone_number(v)


# ---------- Responses ----------

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
