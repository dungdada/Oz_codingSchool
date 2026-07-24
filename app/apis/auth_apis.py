from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.auth.jwt import create_token, decode_token
from app.core.config import settings
from app.core.db.databases import async_get_db
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse

router = APIRouter(prefix="/api/v1/users", tags=["authentication"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/api/v1/users",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다.",
        )

    access_token = create_token(user.id, token_type="access")
    refresh_token = create_token(user.id, token_type="refresh")
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME),
    ] = None,
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 필요합니다.",
        )
    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return TokenResponse(access_token=create_token(user_id, token_type="access"))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/users",
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
