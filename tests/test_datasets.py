from uuid import UUID

import pytest

from application.handlers import add_dataset
from application.services.dataset import DatasetMonitoring
from infrastructure.adapters.in_memory import InMemoryDatasetRepository
from infrastructure.adapters.ods import OpendatasoftDatasetAdapter
from infrastructure.factories.dataset import DatasetAdapterFactory


@pytest.fixture
def datasets():
    repository = InMemoryDatasetRepository([])
    factory = DatasetAdapterFactory()
    return DatasetMonitoring(factory=factory, repository=repository)


def test_create_opendatasoft_dataset(datasets, ods_dataset):
    # Arrange
    dataset_id = add_dataset(
        app=datasets,
        platform_type="opendatasoft",
        dataset=ods_dataset,
    )
    # Act
    result = datasets.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.dataset_id, UUID)
    assert result.snapshot is not None


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


def test_create_datagouv_dataset(datasets, datagouv_dataset):
    # Arrange
    dataset_id = add_dataset(
        app=datasets,
        platform_type="datagouvfr",
        dataset=datagouv_dataset,
    )
    # Act
    result = datasets.repository.get(dataset_id=dataset_id)
    # Assert
    assert isinstance(result.dataset_id, UUID)
    assert result.snapshot is not None


def test_hash_dataset(datasets, ods_dataset):
    # Arrange & Act
    dataset_id = add_dataset(
        app=datasets,
        platform_type="opendatasoft",
        dataset=ods_dataset,
    )
    # Act
    dataset = datasets.repository.get(dataset_id=dataset_id)
    assert (
        dataset.checksum
        == "def80990f5c971702309af7770599485961a45aa4c6baa5bf2238560dbcc04de"
    )
    assert len(dataset.checksum) == 64  # SHA-256 hash length


def test_hash_consistency(datasets, ods_dataset):
    # Arrange
    dataset = datasets.add_dataset(platform_type="opendatasoft", dataset=ods_dataset)
    # Act
    hash1 = dataset.calculate_hash()
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 == hash2  # Hash should be deterministic


def test_hash_shanges_with_data_changes(datasets, ods_dataset):
    # Arrange
    dataset = datasets.add_dataset(platform_type="opendatasoft", dataset=ods_dataset)
    # Act
    hash1 = dataset.calculate_hash()
    dataset.raw["modified"] = "2024-01-01T00:00:00Z"
    hash2 = dataset.calculate_hash()
    # Assert
    assert hash1 != hash2  # Hash should change when data changes
