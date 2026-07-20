from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserResponse, UserSignupRequest

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserSignupRequest,
    db: AsyncSession = Depends(async_get_db),
) -> User:
    """
    REQ-USER-001 회원가입

    사내 의료인, 개발 실무진은 회원가입을 통해 서비스를 이용할 수 있다.
    가입 직후 권한은 PENDING(대기자)으로 설정된다.
    """
    existing_user = await db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일입니다.",
        )

    new_user = User(
        email=payload.email,
        password=hash_password(payload.password),
        name=payload.name,
        department=payload.department,
        gender=payload.gender,
        phone_number=payload.phone_number,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
