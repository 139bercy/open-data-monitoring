import pytest
from fastapi.testclient import TestClient

from domain.auth.aggregate import User
from infrastructure.security import get_password_hash
from interfaces.api.main import api_app
from settings import app as domain_app

client = TestClient(api_app)


@pytest.fixture
def test_user():
    user = User(
        email="test@example.com", hashed_password=get_password_hash("password123"), full_name="Test User", role="admin"
    )
    with domain_app.uow as uow:
        uow.users.save(user)
        uow.commit()
    return user


def test_login_success(test_user):
    # Act
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})
    # Assert
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_password(test_user):
    # Act
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "wrongpassword"})
    # Assert
    assert response.status_code == 401
    assert response.json()["title"] == "Unauthorized"


def test_get_me_protected(test_user):
    # 1. Login to get token
    login_res = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    # 2. Access /me with token
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    # Assert
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert response.json()["full_name"] == "Test User"


def test_get_me_unauthorized():
    # Act
    response = client.get("/api/v1/auth/me")
    # Assert
    assert response.status_code == 401


def test_protected_datasets_route_unauthorized():
    # Act
    response = client.get("/api/v1/datasets/")
    # Assert
    assert response.status_code == 401
