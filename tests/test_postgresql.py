from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.commands.platform import SyncPlatform
from application.handlers import create_platform
from application.services.platform import PlatformMonitoring
from infrastructure.adapters.postgres import PostgresPlatformRepository
from infrastructure.factories.platform import PlatformAdapterFactory


@pytest.fixture
def app(db_transaction):
    return PlatformMonitoring(
        adapter_factory=PlatformAdapterFactory,
        repository=PostgresPlatformRepository(db_transaction),
    )


platform_1 = {
    "name": "My Platform",
    "slug": "my-platform",
    "organization_id": "azertyuiop",
    "type": "test",
    "url": "https://data.mydomain.net",
    "key": "TEST_API_KEY",
}


def test_postgresql_create_platform(app, testfile):
    platform_id = create_platform(app, platform_1)
    platform = app.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_postgresl_sync_platform(app):
    # Arrange
    platform_id = create_platform(app, platform_1)
    # Act
    cmd = SyncPlatform(id=platform_id)
    app.sync_platform(platform_id=cmd.id)
    # Assert
    result = app.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_postgresl_retrieve_platform_with_syncs(app):
    # Arrange
    platform_id = create_platform(app, platform_1)
    cmd = SyncPlatform(id=platform_id)
    app.sync_platform(platform_id=cmd.id)
    # Act
    result = app.repository.get(platform_id)
    # Assert
    assert result.last_sync
    assert len(result.syncs) == 1
