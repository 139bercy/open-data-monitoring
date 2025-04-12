import os
from uuid import UUID

import pytest

from settings import *

from application.projections import TinyDbPlatformRepository
from application.services import DataMonitoring
from application.handlers import create_platform
from infrastructure.factory import AdapterFactory

platform_1 = {
    "name": "data.mydomain.net",
    "type": "test",
    "url": "https://data.mydomain.net",
    "key": "TEST_API_KEY",
}


@pytest.fixture
def app():
    repository = TinyDbPlatformRepository("test.json")
    return DataMonitoring(adapter_factory=AdapterFactory, repository=repository)


def test_create_platform(app: DataMonitoring, testfile):
    # Arrange & Act
    platform_id = create_platform(app, platform_1)
    # Assert
    platform = app.get_platform(platform_id=platform_id)
    assert platform.version == 1
    assert isinstance(platform.id, UUID)


def test_api_key_should_be_hidden(app: DataMonitoring, testfile):
    # Arrange & Act
    platform_id = create_platform(app, platform_1)
    # Assert
    platform = app.get_platform(platform_id=platform_id)
    assert os.environ[platform.key] == "azertyuiop"


def test_sync_platform(app: DataMonitoring, testfile):
    # Arrange
    platform_id = create_platform(app, platform_1)
    # Act
    app.sync_platform(platform_id=platform_id)
    # Assert
    result = app.get_platform(platform_id)
    assert result.version == 2


def test_should_return_all_platforms(app: DataMonitoring, testfile):
    # Arrange
    platform_id = create_platform(app, platform_1)
    app.sync_platform(platform_id=platform_id)
    # Act
    result = app.get_all_platforms()
    # Assert
    assert len(result) == 1


def test_projections(app: DataMonitoring, testfile):
    # Arrange
    platform_id = create_platform(app, platform_1)
    app.sync_platform(platform_id=platform_id)
    # Act
    results = app.get_all_platforms()
    # Assert
    assert len(results) == 1
    assert results[0]["datasets_count"] == 10
