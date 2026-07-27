from pydantic import BaseModel, EmailStr

from app.models.user import Department, Gender, UserRole


class MyPageResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
