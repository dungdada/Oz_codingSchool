from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from jwt import InvalidTokenError

from app.core.config import settings

TokenType = Literal["access", "refresh"]


def _secret_key() -> str:
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY가 설정되지 않았습니다. 팀 노션의 키를 .env에 입력해 주세요."
        )
    return settings.JWT_SECRET_KEY


def create_token(user_id: int, token_type: TokenType) -> str:
    if token_type == "access":
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.now(UTC)
    payload = {
        "user_id": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, _secret_key(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> int:
    try:
        payload = jwt.decode(
            token,
            _secret_key(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except (InvalidTokenError, RuntimeError) as exc:
        raise ValueError("유효하지 않은 인증 토큰입니다.") from exc

    if payload.get("type") != expected_type:
        raise ValueError("토큰 종류가 올바르지 않습니다.")

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise ValueError("토큰의 사용자 정보가 올바르지 않습니다.")
    return user_id
