from uuid import UUID

import pytest

from application.handlers import upsert_dataset
from exceptions import DatasetUnreachableError
from infrastructure.adapters.ods import OpendatasoftDatasetAdapter


def test_create_opendatasoft_dataset(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    dataset_id = upsert_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert len(result.versions) == 1


def test_should_handle_unreachable_dataset(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    dataset_id = upsert_dataset(app=app, platform=platform, dataset=ods_dataset)
    dataset = app.dataset.repository.get(dataset_id=dataset_id)
    # Act
    with pytest.raises(DatasetUnreachableError):
        upsert_dataset(
            app=app,
            platform=platform,
            dataset={"slug": dataset.slug, "sync_status": "failed"},
        )
        # Assert
        result = app.dataset.repository.get(dataset_id=dataset_id)
        assert result.last_sync_status == "failed"


def test_dataset_schema(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    dataset_id = upsert_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.versions[0]["snapshot"] is not None
    assert result.versions[0]["downloads_count"] is not None
    assert result.versions[0]["api_calls_count"] is not None


def test_create_opendatasoft_dataset_platform_does_not_exist(
    app, platform, ods_dataset
):
    # Arrange
    platform.type = "opendatasoft"
    dataset_id = upsert_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)


def test_find_dataset_id_from_url_if_ends_with_dash():
    # Arrange
    url = "https://ny-domain.net/explore/dataset/my-dataset/"
    # Act
    adapter = OpendatasoftDatasetAdapter()
    dataset_id = adapter.find_dataset_id(url=url)
    # Assert
    assert dataset_id == "my-dataset"


def test_find_dataset_id_from_url_if_ends():
    # Arrange
    url = "https://ny-domain.net/explore/dataset/my-dataset"
    # Act
    adapter = OpendatasoftDatasetAdapter()
    dataset_id = adapter.find_dataset_id(url=url)
    # Assert
    assert dataset_id == "my-dataset"


def test_create_datagouv_dataset(app, platform, datagouv_dataset):
    # Arrange
    platform.type = "datagouvfr"
    dataset_id = upsert_dataset(
        app=app,
        platform=platform,
        dataset=datagouv_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.publisher is not None


def test_hash_dataset(app, platform, ods_dataset):
    # Arrange & Act
    platform.type = "opendatasoft"
    dataset_id = upsert_dataset(
        app=app,
        platform=platform,
        dataset=ods_dataset,
    )
    # Act
    dataset = app.dataset.repository.get(dataset_id=dataset_id)
    assert len(dataset.checksum) == 64  # SHA-256 hash length


def test_hash_consistency(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    dataset = app.dataset.add_dataset(platform=platform, dataset=ods_dataset)
    # Act
    hash1 = dataset.calculate_hash()
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 == hash2  # Hash should be deterministic


def test_hash_changes_with_data_changes(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    dataset = app.dataset.add_dataset(platform=platform, dataset=ods_dataset)
    # Act
    hash1 = dataset.calculate_hash()
    dataset.raw["modified"] = "2024-01-01T00:00:00Z"
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 != hash2  # Hash should change when data changes


def test_get_checksum_by_buid(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    upsert_dataset(app=app, platform=platform, dataset=ods_dataset)
    # Act
    checksum = app.dataset.repository.get_checksum_by_buid(
        dataset_buid=ods_dataset["uid"]
    )
    # Assert
    assert checksum is not None
    assert len(checksum) == 64


def test_dataset_version_has_not_changed(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    upsert_dataset(app=app, platform=platform, dataset=ods_dataset)
    # Act & Assert
    upsert_dataset(app=app, platform=platform, dataset=ods_dataset)
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 1


def test_dataset_version_has_changed(app, platform, ods_dataset):
    # Arrange
    platform.type = "opendatasoft"
    upsert_dataset(app=app, platform=platform, dataset=ods_dataset)
    # Act & Assert
    new = {**ods_dataset, "field": "new"}
    upsert_dataset(app=app, platform=platform, dataset=new)
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 2
