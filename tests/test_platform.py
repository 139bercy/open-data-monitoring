from uuid import UUID

import pytest

from infrastructure.adapters.ods import OpendatasoftAdapter
from infrastructure.adapters.in_memory import InMemoryAdapter
from infrastructure.adapters.datagouvfr import DataGouvFrAdapter

from settings import *

from application.queries.platform import TinyDbPlatformRepository
from application.services.platform import DataMonitoring
from application.handlers import create_platform, sync_platform
from infrastructure.factory import AdapterFactory

platform_1 = {
    "name": "My Platform",
    "slug": "my-platform",
    "organization_id": "azertyuiop",
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
    sync_platform(app=app, platform_id=platform_id)
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


def test_factory_should_return_opendatasoft():
    # Arrange & Act
    factory = AdapterFactory.create(
        platform_type="opendatasoft",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(factory, OpendatasoftAdapter)


def test_factory_should_return_data_gouv_fr():
    # Arrange & Act
    factory = AdapterFactory.create(
        platform_type="datagouvfr",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(factory, DataGouvFrAdapter)


def test_factory_should_return_in_memory():
    # Arrange & Act
    factory = AdapterFactory.create(
        platform_type="test",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(factory, InMemoryAdapter)


def test_factory_wrong_platform_type_should_raise_exception():
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        AdapterFactory.create(
            platform_type="whoops",
            url="https://mydomain.net",
            key="TEST_API_KEY",
            slug="slug",
        )
