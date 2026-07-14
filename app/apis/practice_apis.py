import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/practice_api", tags=["practice_api"])

user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!"
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!"
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@"
    }
]

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_password_rules(password: str) -> str:
    if not re.search(r"[A-Z]", password):
        raise ValueError("비밀번호는 대문자를 최소 1자 포함해야 합니다.")
    if not re.search(r"[a-z]", password):
        raise ValueError("비밀번호는 소문자를 최소 1자 포함해야 합니다.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=~`\[\]/;']", password):
        raise ValueError("비밀번호는 특수문자를 최소 1자 포함해야 합니다.")
    return password


def validate_email_rules(email: str) -> str:
    if not EMAIL_REGEX.match(email):
        raise ValueError("이메일 형식이 올바르지 않습니다.")
    return email


# ---------- Schemas ----------

class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=10)
    age: int = Field(..., ge=14)
    email: str = Field(..., max_length=30)
    password: str = Field(..., min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_rules(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_rules(v)


class UserUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=14)
    email: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = Field(None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_email_rules(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password_rules(v)


# ---------- Helpers ----------

def find_user(user_id: int) -> Optional[dict]:
    return next((user for user in user_list if user["id"] == user_id), None)


def get_next_id() -> int:
    if not user_list:
        return 1
    return max(user["id"] for user in user_list) + 1


# ---------- Routes ----------

@router.get("/users", response_model=list[UserResponse])
def get_users():
    return user_list


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = find_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="유효한 id가 아닙니다.")
    return user


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_create: UserCreate):
    if any(user["email"] == user_create.email for user in user_list):
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    new_user = {
        "id": get_next_id(),
        "name": user_create.name,
        "age": user_create.age,
        "email": user_create.email,
        "password": user_create.password,
    }
    user_list.append(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate):
    user = find_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="유효한 id가 아닙니다.")

    update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 항목이 최소 1개 이상 필요합니다.")

    user.update(update_data)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    user = find_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="유효한 id가 아닙니다.")

    user_list.remove(user)
    return {"detail": f"user_id {user_id} 삭제 완료"}
