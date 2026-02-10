from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from interfaces.api.main import api_app
from tests.fixtures.fixtures import platform_1

client = TestClient(api_app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("interfaces.api.routers.platforms.create_platform")
@patch("interfaces.api.routers.platforms.domain_app")
def test_api_create_platform(mock_app, mock_create):
    # Arrange
    new_id = uuid4()
    mock_create.return_value = new_id

    mock_platform = MagicMock()
    mock_platform.id = new_id
    mock_platform.name = "Mock Platform"
    mock_platform.slug = "mock-platform"
    mock_platform.type = "opendatasoft"
    mock_platform.url = "https://mock.com"
    mock_platform.key = "mock-key"

    mock_app.platform.get.return_value = mock_platform

    payload = {**platform_1, "name": "Mock Platform", "type": "opendatasoft"}

    # Act
    response = client.post("/api/v1/platforms/", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(new_id)
    assert data["name"] == "Mock Platform"
    mock_create.assert_called_once()


@patch("interfaces.api.routers.platforms.domain_app")
def test_api_list_platforms(mock_app):
    # Arrange
    platform_id = uuid4()
    mock_platform_dict = {
        "id": platform_id,
        "name": "List Platform",
        "slug": "list-platform",
        "type": "opendatasoft",
        "url": "https://list.com",
        "organization_id": "org-1",
        "key": None,
        "datasets_count": 10,
        "last_sync": None,
        "created_at": None,
        "last_sync_status": None,
        "syncs": [],
    }

    mock_app.platform.get_all_platforms.return_value = [mock_platform_dict]

    # Act
    response = client.get("/api/v1/platforms/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_platforms"] == 1
    assert data["platforms"][0]["slug"] == "list-platform"


@patch("interfaces.api.routers.common.domain_app")
def test_get_publishers_stats_mock(mock_app):
    # Arrange
    mock_app.dataset.repository.get_publishers_stats.return_value = [{"publisher": "Mocked Pub", "dataset_count": 5}]

    # Act
    response = client.get("/api/v1/common/publishers")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_publishers"] == 1
    assert data["publishers"][0]["publisher"] == "Mocked Pub"


@patch("interfaces.api.routers.datasets.domain_app")
def test_api_list_datasets_tests(mock_app):
    # Arrange
    from datetime import datetime

    now = datetime.now()

    mock_dataset_raw = {
        "id": uuid4(),
        "timestamp": now,
        "buid": "buid-test",
        "slug": "dataset-test",
        "page": "https://data.com/test",
        "publisher": "Gov",
        "published": True,
        "restricted": False,
        "last_sync": now,
        "last_sync_status": "success",
        "created": now,
        "modified": now,
        "deleted": False,
    }

    # Mock the database client fetchall call
    mock_app.dataset.repository.client.fetchall.return_value = [mock_dataset_raw]

    # Act
    response = client.get("/api/v1/datasets/tests")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_datasets"] == 1
    assert data["datasets"][0]["slug"] == "dataset-test"


@patch("interfaces.api.routers.datasets.domain_app")
def test_api_list_datasets(mock_app):
    # Arrange
    mock_item = {
        "id": uuid4(),
        "platform_id": uuid4(),
        "buid": "test-buid",
        "slug": "test-slug",
        "publisher": "Test Publisher",
        "title": "Test Title",
        "timestamp": None,
        "created": "2024-01-01T12:00:00",
        "modified": "2024-01-01T12:00:00",
        "restricted": False,
        "published": True,
        "downloads_count": 10,
        "api_calls_count": 5,
        "versions_count": 1,
        "page": "https://test.com",
        "last_sync": None,
        "last_sync_status": "success",
        "deleted": False,
        "quality": {"has_description": True, "is_slug_valid": True, "evaluation_results": None},
    }

    mock_app.dataset.repository.search.return_value = ([mock_item], 1)

    # Act
    response = client.get("/api/v1/datasets/?q=test&sort_by=modified&order=desc&page=1&page_size=25")

    # Assert
    assert response.status_code == 200, f"Error: {response.status_code} - {response.json()}"
    data = response.json()
    assert data["total_datasets"] == 1
    assert len(data["datasets"]) == 1
    assert data["datasets"][0]["title"] == "Test Title"
    mock_app.dataset.repository.search.assert_called_once()
