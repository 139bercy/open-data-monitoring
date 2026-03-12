import os
from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.handlers import find_platform_from_url
from application.use_cases.create_platform import CreatePlatformCommand, CreatePlatformUseCase
from application.use_cases.sync_platform import SyncPlatformCommand, SyncPlatformUseCase
from infrastructure.adapters.platforms.datagouvfr import DataGouvPlatformAdapter
from infrastructure.adapters.platforms.in_memory import InMemoryAdapter
from infrastructure.adapters.platforms.ods import OpendatasoftPlatformAdapter
from infrastructure.factories.platform import PlatformAdapterFactory
from tests.fixtures.fixtures import platform_1


def test_create_platform(app):
    # Arrange & Act
    platform_id = CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    # Assert
    platform = app.platform.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_api_key_should_be_hidden(app):
    # Arrange & Act
    platform_id = CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    # Assert
    platform = app.platform.get(platform_id=platform_id)
    assert os.environ[platform.key] == "azertyuiop"


def test_find_platform_from_url(app):
    # Arrange
    platform_id = CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    # Act
    platform = find_platform_from_url(app=app, url="https://data.mydomain.net")
    # Assert
    assert platform.name == "My Platform"


def test_should_return_all_platforms(app):
    # Arrange
    CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1))
    # Act
    result = app.platform.get_all_platforms()
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
    assert isinstance(adapter, OpendatasoftPlatformAdapter)


def test_factory_should_return_data_gouv_fr():
    # Arrange & Act
    factory = PlatformAdapterFactory()
    adapter = factory.create(
        platform_type="datagouvfr",
        url="http://test.com",
        key="key",
        slug="slug",
    )
    assert isinstance(adapter, DataGouvPlatformAdapter)


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


def test_get_platform_by_domain(app):
    # Arrange & Act
    CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1))
    result = app.platform.repository.get_by_domain("mydomain.net")
    assert str(result.slug) == "my-platform"


def test_sync_platform(app):
    # Arrange
    platform_id = CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    # Act
    SyncPlatformUseCase(uow=app.uow).handle(SyncPlatformCommand(platform_id=platform_id))
    # Assert
    result = app.platform.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_retrieve_platform_with_syncs(app):
    # Arrange
    platform_id = CreatePlatformUseCase(uow=app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    SyncPlatformUseCase(uow=app.uow).handle(SyncPlatformCommand(platform_id=platform_id))
    # Act
    result = app.platform.repository.get(platform_id)
    # Assert
    assert result.last_sync == datetime(2025, 1, 1, 12, 0)
    assert len(result.syncs) == 1
