from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import Department, Gender, UserRole


class PatientListItem(BaseModel):
    id: int
    name: str
    age: int
    gender: Gender
    phone_number: str
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class AdminUserListItem(BaseModel):
    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    users: list[AdminUserListItem]
    total: int
    page: int
    size: int
