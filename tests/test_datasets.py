from uuid import UUID

from application.use_cases.check_deleted_datasets import (
    CheckDeletedDatasetsCommand,
    CheckDeletedDatasetsUseCase,
)
from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase
from domain.platform.aggregate import Platform
from infrastructure.adapters.datasets.ods import OpendatasoftDatasetAdapter


def test_create_opendatasoft_dataset(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert len(result.versions) == 1
    assert result.quality.has_description is not None
    print(result.quality)


def test_should_handle_unreachable_dataset(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    dataset = app.dataset.repository.get(dataset_id=dataset_id)
    # Act
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=ods_platform,
            platform_dataset_id=dataset.slug,
            raw_data={"slug": dataset.slug, "sync_status": "failed"},
        )
    )
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.last_sync_status == "failed"


def test_dataset_schema(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.versions[0]["snapshot"] is not None
    assert result.versions[0]["downloads_count"] is not None
    assert result.versions[0]["api_calls_count"] is not None


def test_create_opendatasoft_dataset_platform_does_not_exist(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
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


def test_create_datagouv_dataset(app, datagouv_platform, datagouv_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_id = result.dataset_id
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.publisher is not None


def test_hash_dataset(app, ods_platform, ods_dataset):
    # Arrange & Act
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    dataset = app.dataset.repository.get(dataset_id=dataset_id)
    assert len(dataset.checksum) == 64  # SHA-256 hash length


def test_hash_consistency(app, ods_platform, ods_dataset):
    # Arrange
    dataset = app.dataset.add_dataset(platform=ods_platform, dataset=ods_dataset, adapter=OpendatasoftDatasetAdapter())
    # Act
    hash1 = dataset.calculate_hash()
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 == hash2  # Hash should be deterministic


def test_hash_changes_with_data_changes(app, ods_platform, ods_dataset):
    # Arrange
    dataset = app.dataset.add_dataset(platform=ods_platform, dataset=ods_dataset, adapter=OpendatasoftDatasetAdapter())
    # Act
    hash1 = dataset.calculate_hash()
    dataset.title = "New Title"
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 != hash2  # Hash should change when structural data changes


def test_get_checksum_by_buid(app, ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    # Act
    checksum = app.dataset.repository.get_checksum_by_buid(dataset_buid=ods_dataset["uid"])
    # Assert
    assert checksum is not None
    assert len(checksum) == 64


def test_dataset_version_has_not_changed(app, ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    # Act & Assert
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 1


def test_dataset_version_has_changed(app, ods_platform, ods_dataset):
    # Arrange
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    # Act & Assert - Change title to trigger checksum change
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
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=new)
    )
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 2


def test_dataset_has_been_deleted_on_platform(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    # Act
    crawler = []
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(
        CheckDeletedDatasetsCommand(platform=ods_platform, datasets=crawler)
    )
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_upsert_restores_deleted_dataset(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id

    # Delete it
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(CheckDeletedDatasetsCommand(platform=ods_platform, datasets=[]))
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True

    # Act: Upsert again
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )

    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False


def test_upsert_restores_and_updates_deleted_dataset(app, ods_platform, ods_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(CheckDeletedDatasetsCommand(platform=ods_platform, datasets=[]))

    # Act: Upsert with CHANGES (inspired by data-eco.json structure)
    new_data = {
        **ods_dataset,
        "metas": {**ods_dataset["metas"], "default": {**ods_dataset["metas"]["default"], "title": "Updated Title"}},
    }
    SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=new_data["uid"], raw_data=new_data)
    )

    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False
    assert len(result.versions) == 2


def test_check_deletions_isolation_between_platforms(app, ods_platform, ods_dataset):
    # Arrange: Create dataset for Platform A
    ods_platform.id = UUID("11111111-1111-1111-1111-111111111111")
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_a_id = result.dataset_id

    # Create Platform B
    platform_b = Platform(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        name="Platform B",
        slug="platform-b",
        type="opendatasoft",
        url="http://platform-b.com",
        organization_id="org-b",
        key="key-b",
    )
    dataset_b_data = {**ods_dataset, "uid": "dataset-b", "dataset_id": "dataset-b"}
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=platform_b, platform_dataset_id=dataset_b_data["uid"], raw_data=dataset_b_data)
    )
    dataset_b_id = result.dataset_id

    # Act: Sync deletions for Platform A only (passing its dataset)
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(
        CheckDeletedDatasetsCommand(platform=ods_platform, datasets=[ods_dataset])
    )

    # Assert: Platform B dataset should be UNTOUCHED (still active)
    # even if not present in the crawler results of Platform A
    dataset_b = app.dataset.repository.get(dataset_id=dataset_b_id)
    assert dataset_b.is_deleted is False


def test_check_deletions_supports_datagouv_id_format(app, datagouv_platform, datagouv_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_id = result.dataset_id

    # Act: Sync using "id" key in crawler result
    crawler_results = [{"id": datagouv_dataset["id"]}]
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(
        CheckDeletedDatasetsCommand(platform=datagouv_platform, datasets=crawler_results)
    )

    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False

    # Verify deletion works with "id" key too
    CheckDeletedDatasetsUseCase(uow=app.uow).handle(
        CheckDeletedDatasetsCommand(platform=datagouv_platform, datasets=[])
    )
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_upsert_supports_null_quality_counts(app, ods_platform, ods_dataset):
    # Arrange
    incomplete_dataset = {**ods_dataset, "api_call_count": None, "download_count": None}
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=ods_platform, platform_dataset_id=incomplete_dataset["uid"], raw_data=incomplete_dataset
        )
    )
    dataset_id = result.dataset_id

    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)

    # Assert
    assert result.quality.api_calls_count is None


def test_ods_underscore_quality_check(app, ods_platform, ods_dataset):
    # Arrange: Dataset ID with underscores
    dataset_with_underscore = {**ods_dataset, "dataset_id": "my_dataset_with_underscores"}
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=ods_platform,
            platform_dataset_id=dataset_with_underscore["dataset_id"],
            raw_data=dataset_with_underscore,
        )
    )
    dataset_id = result.dataset_id

    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)

    # Assert
    assert result.quality.is_slug_valid is False


def test_ods_clean_slug_quality_check(app, ods_platform, ods_dataset):
    # Arrange: Dataset ID without underscores
    dataset_clean = {**ods_dataset, "dataset_id": "my-clean-dataset"}
    result = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=ods_platform, platform_dataset_id=dataset_clean["dataset_id"], raw_data=dataset_clean
        )
    )
    dataset_id = result.dataset_id

    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)

    # Assert
    assert result.quality.is_slug_valid is True


def test_link_datasets(app, ods_platform, ods_dataset, datagouv_platform, datagouv_dataset):
    # Arrange
    ods_dataset["metadata"] = {
        "default": {"source": f"https://www.data.gouv.fr/fr/datasets/{datagouv_dataset['slug']}/"}
    }
    result1 = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(platform=ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    ods_dataset_id = result1.dataset_id
    result2 = SyncDatasetUseCase(uow=app.uow).handle(
        SyncDatasetCommand(
            platform=datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    datagouv_dataset_id = result2.dataset_id
    # 4. Trigger linking
    app.dataset.link_datasets(dataset_or_id=ods_dataset_id)

    # 5. Verify linking
    result = app.dataset.repository.get(dataset_id=ods_dataset_id)
    # Assert
    assert result.linked_dataset_id == datagouv_dataset_id
