from io import BytesIO
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from interfaces.api.main import api_app
from tests.fixtures.fixtures import platform_1

client = TestClient(api_app)

@pytest.fixture
def mock_platforms_router():
    with patch("interfaces.api.routers.platforms.domain_app") as mock_app, \
         patch("interfaces.api.routers.platforms.CreatePlatformUseCase") as mock_uc:
        yield mock_app, mock_uc

@pytest.fixture
def mock_datasets_router():
    with patch("interfaces.api.routers.datasets.domain_app") as mock_app:
        yield mock_app

def test_health_check():
    # Act
    response = client.get("/health")
    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_create_platform(mock_platforms_router):
    # Arrange
    mock_app, mock_uc = mock_platforms_router
    new_id = uuid4()
    mock_uc.return_value.handle.return_value = MagicMock(platform_id=new_id, status="success")
    p = MagicMock()
    p.id, p.name, p.slug, p.type, p.url, p.key = new_id, "M", "s", "opendatasoft", "https://m.com", "k"
    mock_app.platform.get.return_value = p
    # Act
    res = client.post("/api/v1/platforms/", json={**platform_1, "name": "M", "type": "opendatasoft"})
    # Assert
    assert res.status_code == 200
    assert res.json()["id"] == str(new_id)

def test_api_list_platforms(mock_platforms_router):
    # Arrange
    mock_app, _ = mock_platforms_router
    p_id = uuid4()
    mock_app.platform.get_all_platforms.return_value = [{"id": p_id, "name": "L", "slug": "l", "type": "opendatasoft", "url": "https://l.com", "organization_id": "o", "key": None, "datasets_count": 0, "last_sync": None, "created_at": None, "last_sync_status": None, "syncs": []}]
    # Act
    res = client.get("/api/v1/platforms/")
    # Assert
    assert res.status_code == 200
    assert res.json()["total_platforms"] == 1

def test_get_publishers_stats_mock():
    with patch("interfaces.api.routers.common.domain_app") as mock_app:
        # Arrange
        mock_app.dataset.repository.get_publishers_stats.return_value = [{"publisher": "P", "dataset_count": 5}]
        # Act
        res = client.get("/api/v1/common/publishers")
        # Assert
        assert res.status_code == 200
        assert res.json()["total_publishers"] == 1

def test_api_list_datasets_tests(mock_datasets_router):
    # Arrange
    mock_app, now = mock_datasets_router, datetime.now()
    mock_app.dataset.repository.client.fetchall.return_value = [{"id": uuid4(), "platform_id": uuid4(), "timestamp": now, "buid": "b", "slug": "s", "page": "https://h.com", "publisher": "P", "published": True, "restricted": False, "last_sync": now, "last_sync_status": "s", "created": now, "modified": now, "deleted": False}]
    # Act
    res = client.get("/api/v1/datasets/tests")
    # Assert
    assert res.status_code == 200
    assert res.json()["total_datasets"] == 1

def test_api_list_datasets(mock_datasets_router):
    # Arrange
    mock_app = mock_datasets_router
    now = datetime.now()
    item = {"id": uuid4(), "platform_id": uuid4(), "buid": "b", "slug": "s", "publisher": "P", "title": "T", "timestamp": now, "created": now, "modified": now, "restricted": False, "published": True, "downloads_count": 0, "api_calls_count": 0, "versions_count": 1, "page": "https://h.com", "last_sync": now, "last_sync_status": "s", "deleted": False, "quality": {"has_description": True, "is_slug_valid": True, "evaluation_results": None}}
    mock_app.dataset.repository.search.return_value = ([item], 1)
    # Act
    res = client.get("/api/v1/datasets/?q=t")
    # Assert
    assert res.status_code == 200
    assert res.json()["total_datasets"] == 1

def test_get_audit_report(mock_datasets_router):
    # Arrange
    mock_app = mock_datasets_router
    d_id = uuid4()
    p = MagicMock()
    p.id, p.slug = d_id, "s"
    mock_app.dataset.repository.get.return_value = p
    with patch("application.services.headless_report.PlaywrightReportGenerator") as mock_gen_cls:
        mock_gen_cls.return_value.generate_audit_report = AsyncMock(return_value=BytesIO(b"%PDF"))
        # Act
        res = client.get(f"/api/v1/datasets/{d_id}/audit-report")
    # Assert
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF")
