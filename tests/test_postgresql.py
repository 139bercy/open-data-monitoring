from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.commands.platform import SyncPlatform
from application.handlers import check_deleted_datasets, create_platform, upsert_dataset
from infrastructure.adapters.datasets.ods import OpendatasoftDatasetAdapter
from tests.fixtures.fixtures import platform_1


def test_postgresql_create_platform(pg_app):
    platform_id = create_platform(pg_app, platform_1)
    platform = pg_app.platform.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_postgresql_get_platform_by_domain(pg_app):
    # Arrange
    create_platform(pg_app, platform_1)
    # Act
    result = pg_app.platform.repository.get_by_domain("mydomain.net")
    # Assert
    assert str(result.slug) == "my-platform"


def test_postgresl_sync_platform(pg_app):
    # Arrange
    platform_id = create_platform(pg_app, platform_1)
    # Act
    cmd = SyncPlatform(id=platform_id)
    pg_app.platform.sync_platform(platform_id=cmd.id)
    # Assert
    result = pg_app.platform.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_postgresl_retrieve_platform_with_syncs(pg_app):
    # Arrange
    platform_id = create_platform(pg_app, platform_1)
    cmd = SyncPlatform(id=platform_id)
    pg_app.platform.sync_platform(platform_id=cmd.id)
    # Act
    result = pg_app.platform.repository.get(platform_id)
    # Assert
    assert result.last_sync
    assert len(result.syncs) == 1


def test_postgresql_create_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=pg_app,
        platform=pg_ods_platform,
        dataset=ods_dataset,
    )
    # Act
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.id == dataset_id
    assert result.last_sync_status == "success"
    assert result.quality.has_description is not None


def test_postgresql_get_dataset_checksum_by_buid(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    upsert_dataset(
        app=pg_app,
        platform=pg_ods_platform,
        dataset=ods_dataset,
    )
    # Act
    checksum = pg_app.dataset.repository.get_checksum_by_buid(dataset_buid=ods_dataset["uid"])
    # Assert
    assert len(checksum) == 64


def test_postgresql_dataset_has_changed(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=pg_app,
        platform=pg_ods_platform,
        dataset=ods_dataset,
    )
    # Act
    new = {**ods_dataset, "updated_at": "2024-01-01T12:00:00+00:00"}
    upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=new)
    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.id == dataset_id
    assert len(result.versions) == 2


def test_postgresql_should_handle_unreachable_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=ods_dataset)
    dataset = pg_app.dataset.repository.get(dataset_id=dataset_id)
    # Act
    upsert_dataset(
        app=pg_app,
        platform=pg_ods_platform,
        dataset={"slug": dataset.slug, "sync_status": "failed"},
    )
    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.last_sync_status == "failed"


def test_postgresql_add_dataset_should_raise_an_error_on_fk_violation(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    pg_ods_platform.id = UUID("00000000-0000-0000-0000-000000000000")
    dataset = pg_app.dataset.add_dataset(
        platform=pg_ods_platform, dataset=ods_dataset, adapter=OpendatasoftDatasetAdapter()
    )
    # Act & Assert
    with pytest.raises(Exception):
        pg_app.dataset.repository.add(dataset)


def test_postgres_dataset_has_been_deleted_on_platform(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=ods_dataset)
    # Act
    check_deleted_datasets(app=pg_app, platform=pg_ods_platform, datasets=[])
    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_postgresql_upsert_supports_null_quality_counts(pg_app, pg_ods_platform, ods_dataset):
    # Arrange: Dataset with NULL counts
    incomplete_dataset = {**ods_dataset, "api_call_count": None, "download_count": None}
    dataset_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=incomplete_dataset)

    # Act
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)

    # Assert
    assert result.quality.downloads_count is None
    assert result.quality.api_calls_count is None


def test_postgresql_upsert_restores_and_updates_deleted_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=ods_dataset)

    # Delete it
    check_deleted_datasets(app=pg_app, platform=pg_ods_platform, datasets=[])

    # Act: Upsert with CHANGES
    new_data = {
        **ods_dataset,
        "metas": {**ods_dataset["metas"], "default": {**ods_dataset["metas"]["default"], "title": "Updated SQL Title"}},
    }
    upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=new_data)

    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False
    assert len(result.versions) == 2


def test_postgresql_check_deletions_isolation_between_platforms(pg_app, pg_ods_platform, ods_dataset):
    # Arrange: Create dataset for Platform A (pg_ods_platform)
    upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=ods_dataset)

    # Create Platform B
    platform_b_data = {
        **platform_1,
        "name": "Platform B",
        "slug": "platform-b",
        "url": "http://platform-b.com",
        "type": "opendatasoft",
    }
    platform_b_id = create_platform(pg_app, platform_b_data)
    platform_b = pg_app.platform.get(platform_id=platform_b_id)

    dataset_b_data = {**ods_dataset, "uid": "dataset-b", "dataset_id": "dataset-b"}
    dataset_b_id = upsert_dataset(app=pg_app, platform=platform_b, dataset=dataset_b_data)

    # Act: Sync deletions for Platform A only
    check_deleted_datasets(app=pg_app, platform=pg_ods_platform, datasets=[ods_dataset])

    # Assert: Platform B dataset should be UNTOUCHED
    result_b = pg_app.dataset.repository.get(dataset_id=dataset_b_id)
    assert result_b.is_deleted is False
