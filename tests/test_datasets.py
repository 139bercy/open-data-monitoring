from uuid import UUID

from application.handlers import upsert_dataset, check_deleted_datasets
from domain.platform.aggregate import Platform
from infrastructure.adapters.datasets.ods import OpendatasoftDatasetAdapter


def test_create_opendatasoft_dataset(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=app,
        platform=ods_platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert len(result.versions) == 1
    assert result.quality.has_description is not None
    print(result.quality)


def test_should_handle_unreachable_dataset(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    dataset = app.dataset.repository.get(dataset_id=dataset_id)
    # Act
    upsert_dataset(
        app=app,
        platform=ods_platform,
        dataset={"slug": dataset.slug, "sync_status": "failed"},
    )
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.last_sync_status == "failed"


def test_dataset_schema(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=app,
        platform=ods_platform,
        dataset=ods_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.versions[0]["snapshot"] is not None
    assert result.versions[0]["downloads_count"] is not None
    assert result.versions[0]["api_calls_count"] is not None


def test_create_opendatasoft_dataset_platform_does_not_exist(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=app,
        platform=ods_platform,
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


def test_create_datagouv_dataset(app, datagouv_platform, datagouv_dataset):
    # Arrange
    dataset_id = upsert_dataset(
        app=app,
        platform=datagouv_platform,
        dataset=datagouv_dataset,
    )
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.id, UUID)
    assert result.publisher is not None


def test_hash_dataset(app, ods_platform, ods_dataset):
    # Arrange & Act
    dataset_id = upsert_dataset(
        app=app,
        platform=ods_platform,
        dataset=ods_dataset,
    )
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
    dataset.raw["modified"] = "2024-01-01T00:00:00Z"
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 != hash2  # Hash should change when data changes


def test_get_checksum_by_buid(app, ods_platform, ods_dataset):
    # Arrange
    upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    # Act
    checksum = app.dataset.repository.get_checksum_by_buid(dataset_buid=ods_dataset["uid"])
    # Assert
    assert checksum is not None
    assert len(checksum) == 64


def test_dataset_version_has_not_changed(app, ods_platform, ods_dataset):
    # Arrange
    upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    # Act & Assert
    upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 1


def test_dataset_version_has_changed(app, ods_platform, ods_dataset):
    # Arrange
    upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    # Act & Assert
    new = {**ods_dataset, "field": "new"}
    upsert_dataset(app=app, platform=ods_platform, dataset=new)
    assert len(app.dataset.repository.db) == 1
    assert len(app.dataset.repository.versions) == 2


def test_dataset_has_been_deleted_on_platform(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    # Act
    crawler = []
    check_deleted_datasets(app=app, platform=ods_platform, datasets=crawler)
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_upsert_restores_deleted_dataset(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    
    # Delete it
    check_deleted_datasets(app=app, platform=ods_platform, datasets=[])
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True
    
    # Act: Upsert again
    upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False


def test_upsert_restores_and_updates_deleted_dataset(app, ods_platform, ods_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    check_deleted_datasets(app=app, platform=ods_platform, datasets=[])
    
    # Act: Upsert with CHANGES (inspired by data-eco.json structure)
    new_data = {**ods_dataset, "metas": {**ods_dataset["metas"], "default": {**ods_dataset["metas"]["default"], "title": "Updated Title"}}}
    upsert_dataset(app=app, platform=ods_platform, dataset=new_data)
    
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False
    assert len(result.versions) == 2


def test_check_deletions_isolation_between_platforms(app, ods_platform, ods_dataset):
    # Arrange: Create dataset for Platform A
    ods_platform.id = UUID("11111111-1111-1111-1111-111111111111")
    dataset_a_id = upsert_dataset(app=app, platform=ods_platform, dataset=ods_dataset)
    
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
    dataset_b_id = upsert_dataset(app=app, platform=platform_b, dataset=dataset_b_data)
    
    # Act: Sync deletions for Platform A only (passing its dataset)
    check_deleted_datasets(app=app, platform=ods_platform, datasets=[ods_dataset])
    
    # Assert: Platform B dataset should be UNTOUCHED (still active)
    # even if not present in the crawler results of Platform A
    dataset_b = app.dataset.repository.get(dataset_id=dataset_b_id)
    assert dataset_b.is_deleted is False


def test_check_deletions_supports_datagouv_id_format(app, datagouv_platform, datagouv_dataset):
    # Arrange
    dataset_id = upsert_dataset(app=app, platform=datagouv_platform, dataset=datagouv_dataset)
    
    # Act: Sync using "id" key in crawler result
    crawler_results = [{"id": datagouv_dataset["id"]}]
    check_deleted_datasets(app=app, platform=datagouv_platform, datasets=crawler_results)
    
    # Assert
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is False
    
    # Verify deletion works with "id" key too
    check_deleted_datasets(app=app, platform=datagouv_platform, datasets=[])
    result = app.dataset.repository.get(dataset_id=dataset_id)
    assert result.is_deleted is True


def test_upsert_supports_null_quality_counts(app, ods_platform, ods_dataset):
    # Arrange
    incomplete_dataset = {**ods_dataset, "api_call_count": None, "download_count": None}
    dataset_id = upsert_dataset(app=app, platform=ods_platform, dataset=incomplete_dataset)
    
    # Act
    result = app.dataset.repository.get(dataset_id=dataset_id)
    
    # Assert
    assert result.quality.downloads_count is None
    assert result.quality.api_calls_count is None
