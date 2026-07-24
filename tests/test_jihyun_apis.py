from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.db.databases import async_get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import Department, Gender, UserRole


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeExecuteResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return FakeScalarResult(self.values)


class FakeSession:
    def __init__(self, *, scalar_values=None, execute_values=None):
        self.scalar_values = list(scalar_values or [])
        self.execute_values = list(execute_values or [])

    async def scalar(self, _query):
        return self.scalar_values.pop(0) if self.scalar_values else None

    async def execute(self, _query):
        return FakeExecuteResult(self.execute_values)


def make_user(*, role=UserRole.STAFF, password="Password1234!"):
    return SimpleNamespace(
        id=1,
        email="jihyun@example.com",
        password=hash_password(password),
        name="김지현",
        department=Department.DEVELOPER,
        gender=Gender.FEMALE,
        phone_number="010-1234-5678",
        role=role,
        is_active=True,
    )


def override_db(session):
    async def _override():
        yield session

    return _override


def override_user(user):
    async def _override():
        return user

    return _override


def setup_function():
    app.dependency_overrides.clear()
    settings.JWT_SECRET_KEY = "test-secret-key-with-at-least-32-characters"


def teardown_function():
    app.dependency_overrides.clear()


def test_login_and_logout():
    user = make_user()
    app.dependency_overrides[async_get_db] = override_db(
        FakeSession(scalar_values=[user])
    )

    with TestClient(app) as client:
        login_response = client.post(
            "/api/v1/users/login",
            data={"username": user.email, "password": "Password1234!"},
        )

        assert login_response.status_code == 200
        assert login_response.json()["token_type"] == "bearer"
        assert login_response.json()["access_token"]
        assert "refresh_token" in login_response.cookies

        app.dependency_overrides[get_current_user] = override_user(user)
        logout_response = client.post(
            "/api/v1/users/logout",
            headers={"Authorization": "Bearer test-token"},
        )

        assert logout_response.status_code == 204
        assert "refresh_token=" in logout_response.headers["set-cookie"]


def test_patient_list_filters_and_response():
    user = make_user()
    patient = SimpleNamespace(
        id=15,
        name="김환자",
        age=45,
        gender=Gender.FEMALE,
        phone_number="010-9876-5432",
        created_at=datetime.now(UTC),
        updated_at=None,
    )
    app.dependency_overrides[get_current_user] = override_user(user)
    app.dependency_overrides[async_get_db] = override_db(
        FakeSession(execute_values=[patient])
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/patients",
            params={
                "name": "김",
                "gender": "female",
                "min_age": 20,
                "max_age": 60,
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()[0]["name"] == "김환자"


def test_patient_list_rejects_invalid_age_range():
    user = make_user()
    app.dependency_overrides[get_current_user] = override_user(user)
    app.dependency_overrides[async_get_db] = override_db(FakeSession())

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/patients?min_age=60&max_age=20",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "min_age는 max_age보다 클 수 없습니다."


def test_admin_user_list_and_permission_check():
    admin = make_user(role=UserRole.ADMIN)
    listed_user = make_user()
    app.dependency_overrides[get_current_user] = override_user(admin)
    app.dependency_overrides[async_get_db] = override_db(
        FakeSession(scalar_values=[1], execute_values=[listed_user])
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/admin/users?keyword=지현&page=1&size=10",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["users"][0]["email"] == "jihyun@example.com"

    staff = make_user(role=UserRole.STAFF)
    app.dependency_overrides[get_current_user] = override_user(staff)
    app.dependency_overrides[async_get_db] = override_db(FakeSession())

    with TestClient(app) as client:
        forbidden = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer test-token"},
        )

        assert forbidden.status_code == 403
