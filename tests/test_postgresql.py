from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.commands.platform import SyncPlatform
from application.handlers import add_dataset, create_platform
from application.services.dataset import DatasetMonitoring
from application.services.platform import PlatformMonitoring
from infrastructure.adapters.postgres import (
    PostgresDatasetRepository,
    PostgresPlatformRepository,
)
from settings import app, client


@pytest.fixture
def platform(db_transaction):
    return PlatformMonitoring(
        repository=PostgresPlatformRepository(client=db_transaction)
    )


@pytest.fixture
def datasets(db_transaction):
    repository = PostgresDatasetRepository(client=db_transaction)
    return DatasetMonitoring(repository=repository)


platform_1 = {
    "name": "My Platform",
    "slug": "my-platform",
    "organization_id": "azertyuiop",
    "type": "test",
    "url": "https://data.mydomain.net",
    "key": "TEST_API_KEY",
}


def test_postgresql_create_platform(platform, testfile):
    platform_id = create_platform(platform, platform_1)
    platform = platform.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_postgresql_get_platform_by_domain(platform, testfile):
    # Arrange
    create_platform(platform, platform_1)
    # Act
    result = platform.repository.get_by_domain("mydomain.net")
    # Assert
    assert result.slug == "my-platform"


def test_postgresl_sync_platform(platform):
    # Arrange
    platform_id = create_platform(platform, platform_1)
    # Act
    cmd = SyncPlatform(id=platform_id)
    platform.sync_platform(platform_id=cmd.id)
    # Assert
    result = platform.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_postgresl_retrieve_platform_with_syncs(platform):
    # Arrange
    platform_id = create_platform(platform, platform_1)
    cmd = SyncPlatform(id=platform_id)
    platform.sync_platform(platform_id=cmd.id)
    # Act
    result = platform.repository.get(platform_id)
    # Assert
    assert result.last_sync
    assert len(result.syncs) == 1


def test_postgresql_create_dataset(db_transaction, ods_dataset):
    # Arrange
    app.dataset.repository = PostgresDatasetRepository(client=db_transaction)
    dataset_id = add_dataset(
        app=app,
        platform_type="opendatasoft",
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.dataset_id, UUID)
    assert result.dataset_id == dataset_id
