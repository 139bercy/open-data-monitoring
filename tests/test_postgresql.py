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
from infrastructure.unit_of_work import PostgresUnitOfWork
from settings import App, app
from tests.fixtures.fixtures import platform_1


@pytest.fixture
def platform_app(db_transaction):
    uow = PostgresUnitOfWork(client=db_transaction)
    return App(uow=uow)


@pytest.fixture
def datasets(db_transaction):
    repository = PostgresDatasetRepository(client=db_transaction)
    return DatasetMonitoring(repository=repository)


def test_postgresql_create_platform(platform_app, testfile):
    platform_id = create_platform(platform_app, platform_1)
    platform = platform_app.platform.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_postgresql_get_platform_by_domain(platform_app, testfile):
    # Arrange
    create_platform(platform_app, platform_1)
    # Act
    result = platform_app.platform.repository.get_by_domain("mydomain.net")
    # Assert
    assert result.slug == "my-platform"


def test_postgresl_sync_platform(platform_app):
    # Arrange
    platform_id = create_platform(platform_app, platform_1)
    # Act
    cmd = SyncPlatform(id=platform_id)
    platform_app.platform.sync_platform(platform_id=cmd.id)
    # Assert
    result = platform_app.platform.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_postgresl_retrieve_platform_with_syncs(platform_app):
    # Arrange
    platform_id = create_platform(platform_app, platform_1)
    cmd = SyncPlatform(id=platform_id)
    platform_app.platform.sync_platform(platform_id=cmd.id)
    # Act
    result = platform_app.platform.repository.get(platform_id)
    # Assert
    assert result.last_sync
    assert len(result.syncs) == 1


def test_postgresql_create_dataset(platform_app, platform, db_transaction, ods_dataset):
    # Arrange
    platform_id = create_platform(platform_app, platform_1)
    platform.id, platform.type = platform_id, "opendatasoft"
    app.dataset.repository = PostgresDatasetRepository(client=db_transaction)
    dataset_id = add_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.dataset_id, UUID)
    assert result.dataset_id == dataset_id


def test_postgresql_get_dataset_checksum_by_buid(platform_app, platform, db_transaction, ods_dataset):
    # Arrange
    platform_id = create_platform(platform_app, platform_1)
    platform.id, platform.type = platform_id, "opendatasoft"
    app.dataset.repository = PostgresDatasetRepository(client=db_transaction)
    dataset_id = add_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    checksum = app.dataset.repository.get_checksum_by_buid(dataset_buid=ods_dataset["uid"])
    # Assert
    assert len(checksum) == 64
