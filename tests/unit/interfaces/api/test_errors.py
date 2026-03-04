import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.datasets.exceptions import DatasetNotFoundError
from domain.platform.exceptions import PlatformNotFoundError
from interfaces.api.errors import register_error_handlers


@pytest.fixture
def client():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/test-not-found")
    async def trigger_not_found():
        raise DatasetNotFoundError("Dataset XYZ not found")

    @app.get("/test-platform-not-found")
    async def trigger_platform_not_found():
        raise PlatformNotFoundError("Platform ABC not found")

    @app.get("/test-value-error")
    async def trigger_value_error():
        raise ValueError("Invalid value provided")

    @app.get("/test-unhandled")
    async def trigger_unhandled():
        raise RuntimeError("Something went wrong")

    return TestClient(app, raise_server_exceptions=False)


def test_dataset_not_found_rfc7807(client):
    response = client.get("/test-not-found")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["type"] == "/probs/not-found"
    assert data["title"] == "Resource Not Found"
    assert data["status"] == 404
    assert "Dataset XYZ not found" in data["detail"]


def test_platform_not_found_rfc7807(client):
    response = client.get("/test-platform-not-found")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["type"] == "/probs/not-found"
    assert data["title"] == "Resource Not Found"


def test_value_error_rfc7807(client):
    response = client.get("/test-value-error")
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["type"] == "/probs/value-error"
    assert data["title"] == "Value Error"


def test_unhandled_exception_rfc7807(client):
    response = client.get("/test-unhandled")
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["type"] == "/probs/internal-server-error"
    assert data["title"] == "Internal Server Error"
    assert data["detail"] == "An unexpected error occurred on the server."
