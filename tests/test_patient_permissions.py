from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.apis.patient_apis import (
    require_internal_user,
    require_medical_staff_or_admin,
)
from app.models.user import Department, UserRole


def make_user(role: UserRole, department: Department):
    return SimpleNamespace(role=role, department=department)


def test_medical_staff_can_create_patient():
    user = make_user(UserRole.STAFF, Department.MEDICAL_TEAM)

    assert require_medical_staff_or_admin(user) is user


def test_non_medical_staff_cannot_create_patient():
    user = make_user(UserRole.STAFF, Department.DEVELOPER)

    with pytest.raises(HTTPException) as error:
        require_medical_staff_or_admin(user)

    assert error.value.status_code == 403


def test_pending_user_cannot_access_patient_api():
    user = make_user(UserRole.PENDING, Department.MEDICAL_TEAM)

    with pytest.raises(HTTPException) as error:
        require_internal_user(user)

    assert error.value.status_code == 403
