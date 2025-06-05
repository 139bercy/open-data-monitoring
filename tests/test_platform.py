from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.commands.platform import SyncPlatform
from application.handlers import create_platform, sync_platform
from infrastructure.adapters.datagouvfr import DataGouvFrAdapter
from infrastructure.adapters.in_memory import InMemoryAdapter
from infrastructure.adapters.ods import OpendatasoftAdapter
from infrastructure.factories.platform import PlatformAdapterFactory
from settings import *

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
    repository = InMemoryPlatformRepository([])
    return PlatformMonitoring(repository=repository)


def test_create_platform(app, testfile):
    # Arrange & Act
    platform_id = create_platform(app, platform_1)
    # Assert
    platform = app.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_api_key_should_be_hidden(app, testfile):
    # Arrange & Act
    platform_id = create_platform(app, platform_1)
    # Assert
    platform = app.get(platform_id=platform_id)
    assert os.environ[platform.key] == "azertyuiop"


def test_should_return_all_platforms(app: PlatformMonitoring, testfile):
    # Arrange
    create_platform(app, platform_1)
    # Act
    result = app.get_all_platforms()
    # Assert
    assert len(result) == 1


def test_factory_should_return_opendatasoft():
    # Arrange & Act
    factory = PlatformAdapterFactory()
    adapter = factory.create(
        platform_type="opendatasoft",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(adapter, OpendatasoftAdapter)


def test_factory_should_return_data_gouv_fr():
    # Arrange & Act
    factory = PlatformAdapterFactory()
    adapter = factory.create(
        platform_type="datagouvfr",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(adapter, DataGouvFrAdapter)


def test_factory_should_return_in_memory():
    # Arrange & Act
    factory = PlatformAdapterFactory()
    adapter = factory.create(
        platform_type="test",
        url="https://mydomain.net",
        key="TEST_API_KEY",
        slug="slug",
    )
    assert isinstance(adapter, InMemoryAdapter)


def test_factory_wrong_platform_type_should_raise_exception():
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        factory = PlatformAdapterFactory()
        factory.create(
            platform_type="whoops",
            url="https://mydomain.net",
            key="TEST_API_KEY",
            slug="slug",
        )


def test_get_platform_by_domain(app, testfile):
    # Arrange & Act
    create_platform(app, platform_1)
    result = app.repository.get_by_domain("mydomain.net")
    assert result.slug == "my-platform"


def test_sync_platform(app):
    # Arrange
    platform_id = create_platform(app, platform_1)
    # Act
    sync_platform(app, platform_id=platform_id)
    # Assert
    result = app.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_retrieve_platform_with_syncs(app):
    # Arrange
    platform_id = create_platform(app, platform_1)
    cmd = SyncPlatform(id=platform_id)
    app.sync_platform(platform_id=cmd.id)
    # Act
    result = app.repository.get(platform_id)
    # Assert
    assert result.last_sync == datetime(2025, 1, 1, 12, 0)
    assert len(result.syncs) == 1
