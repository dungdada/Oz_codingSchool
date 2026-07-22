from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi import HTTPException

from app.apis.admin_user_api import require_admin_user
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import UserRole


def test_require_admin_user_accepts_db_admin() -> None:
    admin = SimpleNamespace(role=UserRole.ADMIN)

    assert require_admin_user(admin) is admin


def test_require_admin_user_rejects_authenticated_non_admin() -> None:
    staff = SimpleNamespace(role=UserRole.STAFF)

    with pytest.raises(HTTPException) as exc_info:
        require_admin_user(staff)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_jwt() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid-token", AsyncMock())

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_get_current_user_loads_user_from_database() -> None:
    user = SimpleNamespace(id=7, is_active=True, role=UserRole.ADMIN)
    scalar_result = SimpleNamespace(scalar_one_or_none=lambda: user)
    db = AsyncMock()
    db.execute.return_value = scalar_result
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert await get_current_user(token, db) is user
    db.execute.assert_awaited_once()
