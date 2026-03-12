from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time

from application.use_cases.check_deleted_datasets import (
    CheckDeletedDatasetsCommand,
    CheckDeletedDatasetsUseCase,
)
from application.use_cases.create_platform import CreatePlatformCommand, CreatePlatformUseCase
from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase
from application.use_cases.sync_platform import SyncPlatformCommand, SyncPlatformUseCase
from infrastructure.adapters.datasets.ods import OpendatasoftDatasetAdapter
from tests.fixtures.fixtures import platform_1


def test_postgresql_create_platform(pg_app):
    use_case = CreatePlatformUseCase(uow=pg_app.uow)
    command = CreatePlatformCommand(**platform_1)
    output = use_case.handle(command)
    platform_id = output.platform_id
    platform = pg_app.platform.get(platform_id=platform_id)
    assert isinstance(platform.id, UUID)


def test_postgresql_get_platform_by_domain(pg_app):
    # Arrange
    CreatePlatformUseCase(uow=pg_app.uow).handle(CreatePlatformCommand(**platform_1))
    # Act
    result = pg_app.platform.repository.get_by_domain("mydomain.net")
    # Assert
    assert str(result.slug) == "my-platform"


def test_postgresl_sync_platform(pg_app):
    # Arrange
    platform_id = CreatePlatformUseCase(uow=pg_app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    # Act
    SyncPlatformUseCase(uow=pg_app.uow).handle(SyncPlatformCommand(platform_id=platform_id))
    # Assert
    result = pg_app.platform.repository.get(platform_id)
    assert isinstance(result.last_sync, datetime)


@freeze_time("2025-01-01 12:00:00")
def test_postgresl_retrieve_platform_with_syncs(pg_app):
    # Arrange
    platform_id = CreatePlatformUseCase(uow=pg_app.uow).handle(CreatePlatformCommand(**platform_1)).platform_id
    SyncPlatformUseCase(uow=pg_app.uow).handle(SyncPlatformCommand(platform_id=platform_id))
    # Act
    result = pg_app.platform.repository.get(platform_id)
    # Assert
    assert result.last_sync
    assert len(result.syncs) == 1


def test_postgresql_create_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.id == dataset_id
    assert result.last_sync_status == "success"
    assert result.quality.has_description is not None


def test_postgresql_get_dataset_checksum_by_buid(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    # Act
    checksum = pg_app.dataset.repository.get_checksum_by_buid(dataset_buid=ods_dataset["uid"])
    # Assert
    assert len(checksum) == 64


def test_postgresql_dataset_has_changed(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act - Change title to trigger checksum change
    new = {
        **ods_dataset,
        "metadata": {
            **ods_dataset["metadata"],
            "default": {
                **ods_dataset["metadata"]["default"],
                "title": "New Title That Changes Checksum",
            },
        },
    }
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=new)
    )
    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.id == dataset_id
    assert len(result.versions) == 2


def test_postgresql_should_handle_unreachable_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    dataset = pg_app.dataset.repository.get(dataset_id=dataset_id)
    # Act
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_ods_platform,
            platform_dataset_id=dataset.slug,
            raw_data={"slug": dataset.slug, "sync_status": "failed"},
        )
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
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    CheckDeletedDatasetsUseCase(uow=pg_app.uow).handle(
        CheckDeletedDatasetsCommand(platform=pg_ods_platform, datasets=[])
    )
    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_postgresql_upsert_supports_null_quality_counts(pg_app, pg_ods_platform, ods_dataset):
    # Arrange: Dataset with NULL counts
    incomplete_dataset = {**ods_dataset, "api_call_count": None, "download_count": None}
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_ods_platform, platform_dataset_id=incomplete_dataset["uid"], raw_data=incomplete_dataset
        )
    )
    dataset_id = result.dataset_id

    # Act
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)

    # Assert
    assert result.quality.downloads_count is None
    assert result.quality.api_calls_count is None


def test_postgresql_upsert_restores_and_updates_deleted_dataset(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id

    # Delete it
    CheckDeletedDatasetsUseCase(uow=pg_app.uow).handle(
        CheckDeletedDatasetsCommand(platform=pg_ods_platform, datasets=[])
    )

    # Act: Upsert with CHANGES
    new_data = {
        **ods_dataset,
        "metadata": {
            **ods_dataset["metadata"],
            "default": {**ods_dataset["metadata"]["default"], "title": "Updated SQL Title"},
        },
    }
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=new_data)
    )

    # Assert
    result = pg_app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False
    assert len(result.versions) == 2


def test_postgresql_check_deletions_isolation_between_platforms(pg_app, pg_ods_platform, ods_dataset):
    # Arrange: Create dataset for Platform A (pg_ods_platform)
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )

    # Create Platform B
    platform_b_data = {
        **platform_1,
        "name": "Platform B",
        "slug": "platform-b",
        "url": "http://platform-b.com",
        "type": "opendatasoft",
    }
    res_b = CreatePlatformUseCase(uow=pg_app.uow).handle(CreatePlatformCommand(**platform_b_data))
    platform_b_id = res_b.platform_id
    platform_b = pg_app.platform.get(platform_id=platform_b_id)

    dataset_b_data = {**ods_dataset, "uid": "dataset-b", "dataset_id": "dataset-b"}
    result_b = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=platform_b, platform_dataset_id=dataset_b_data["uid"], raw_data=dataset_b_data)
    )
    dataset_b_id = result_b.dataset_id

    # Act: Sync deletions for Platform A only
    CheckDeletedDatasetsUseCase(uow=pg_app.uow).handle(
        CheckDeletedDatasetsCommand(platform=pg_ods_platform, datasets=[ods_dataset])
    )

    # Assert: Platform B dataset should be UNTOUCHED
    result_b = pg_app.dataset.repository.get(dataset_id=dataset_b_id)
    assert result_b.is_deleted is False


def test_postgresql_get_id_by_slug_globally_with_suffix(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    clean_slug = ods_dataset["dataset_id"]
    suffix_slug = f"{clean_slug}-571796"

    # Act
    id_clean = pg_app.dataset.repository.get_id_by_slug_globally(clean_slug)
    id_suffix = pg_app.dataset.repository.get_id_by_slug_globally(suffix_slug)

    # Assert
    assert id_clean == dataset_id
    assert id_suffix == dataset_id


def test_postgresql_search_by_platform_id(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )

    # Act
    items, total = pg_app.dataset.repository.search(platform_id=str(pg_ods_platform.id))

    # Assert
    assert total == 1
    assert len(items) == 1
    assert items[0]["slug"] == ods_dataset["dataset_id"]


def test_postgresql_search_sorting(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )

    # Act
    # Sort by 'modified' which is present in multiple tables (datasets d, datasets ld)
    # but selected as 'modified' in the main query.
    items, total = pg_app.dataset.repository.search(sort_by="modified", order="desc")

    # Assert
    assert total == 1
    assert len(items) == 1
    assert items[0]["slug"] == ods_dataset["dataset_id"]


def test_postgresql_search_sorting_health_nulls_last(pg_app, pg_ods_platform, ods_dataset):
    # Arrange
    # Dataset 1: Health Score 100
    res1 = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_ods_platform,
            platform_dataset_id="d1",
            raw_data={**ods_dataset, "uid": "d1", "dataset_id": "d1"},
        )
    )
    d1_id = res1.dataset_id
    pg_app.dataset.repository.client.execute(
        "UPDATE dataset_quality SET health_score = 100 WHERE dataset_id = %s", (str(d1_id),)
    )

    # Dataset 2: Health Score 50
    res2 = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_ods_platform,
            platform_dataset_id="d2",
            raw_data={**ods_dataset, "uid": "d2", "dataset_id": "d2"},
        )
    )
    d2_id = res2.dataset_id
    pg_app.dataset.repository.client.execute(
        "UPDATE dataset_quality SET health_score = 50 WHERE dataset_id = %s", (str(d2_id),)
    )

    # Dataset 3: No Health Score (NULL)
    res3 = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_ods_platform,
            platform_dataset_id="d3",
            raw_data={**ods_dataset, "uid": "d3", "dataset_id": "d3"},
        )
    )
    d3_id = res3.dataset_id
    pg_app.dataset.repository.client.execute(
        "UPDATE dataset_quality SET health_score = NULL WHERE dataset_id = %s", (str(d3_id),)
    )

    # Act & Assert: DESC (Best first, NULLs last)
    items_desc, _ = pg_app.dataset.repository.search(sort_by="health_score", order="desc")
    # Order should be: d1 (100), d2 (50), d3 (NULL)
    assert items_desc[0]["slug"] == "d1"
    assert items_desc[1]["slug"] == "d2"
    assert items_desc[2]["slug"] == "d3"

    # Act & Assert: ASC (Worst first, NULLs last)
    items_asc, _ = pg_app.dataset.repository.search(sort_by="health_score", order="asc")
    # Order should be: d2 (50), d1 (100), d3 (NULL)
    assert items_asc[0]["slug"] == "d2"
    assert items_asc[1]["slug"] == "d1"
    assert items_asc[2]["slug"] == "d3"
