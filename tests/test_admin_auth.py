from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth.dependencies import get_current_user, require_admin_user
from app.core.config import settings
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_require_admin_user_accepts_db_admin() -> None:
    admin = SimpleNamespace(role=UserRole.ADMIN)

    assert await require_admin_user(admin) is admin


@pytest.mark.asyncio
async def test_require_admin_user_rejects_authenticated_non_admin() -> None:
    staff = SimpleNamespace(role=UserRole.STAFF)

    with pytest.raises(HTTPException) as exc_info:
        await require_admin_user(staff)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_jwt() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="invalid-token",
            ),
            AsyncMock(),
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_get_current_user_loads_user_from_database() -> None:
    user = SimpleNamespace(id=7, is_active=True, role=UserRole.ADMIN)
    db = AsyncMock()
    db.scalar.return_value = user
    settings.JWT_SECRET_KEY = "test-secret-key-with-at-least-32-characters"
    token = jwt.encode(
        {"user_id": user.id, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert await get_current_user(credentials, db) is user
    db.scalar.assert_awaited_once()
