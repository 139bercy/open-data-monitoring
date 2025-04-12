from uuid import UUID

import pytest

from application.services import DataMonitoring
from application.handlers import create_platform
from infrastructure.factory import AdapterFactory

data_eco = {
    "name": "data.mydomain.net",
    "type": "test",
    "url": "https://data.mydomain.net",
    "key": "azertyuiop"
}


@pytest.fixture
def app():
    return DataMonitoring(adapter_factory=AdapterFactory)


def test_create_platform(app: DataMonitoring):
    # Arrange & Act
    platform_id = create_platform(app, data_eco)
    # Assert
    platform = app.get_platform(platform_id=platform_id)
    assert platform.version == 1
    assert isinstance(platform.id, UUID)


def test_sync_platform(app: DataMonitoring):
    # Arrange
    platform_id = create_platform(app, data_eco)
    # Act
    app.sync_platform(platform_id=platform_id)
    # Assert
    result = app.get_platform(platform_id)
    assert result.version == 2
