from pydantic import BaseModel, ConfigDict, Field

from app.models.user import Department, UserRole


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    department: Department
    phone_number: str
    role: UserRole
    is_active: bool


class AdminUserRoleUpdateRequest(BaseModel):
    user_ids: list[int] = Field(..., min_length=1)
    new_role: UserRole


class AdminUserRoleUpdateResponse(BaseModel):
    updated_count: int
    users: list[AdminUserResponse]
