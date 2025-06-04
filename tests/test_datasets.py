from uuid import UUID

import pytest

from application.handlers import add_dataset
from application.services.dataset import DatasetMonitoring
from infrastructure.adapters.in_memory import InMemoryDatasetRepository
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


def test_find_dataset_id_from_url_if_ends_with_dash(datasets):
    # Arrange
    url = "https://ny-domain.net/explore/dataset/my-dataset/"
    # Act
    datasets.set_adapter(platform_type="opendatasoft")
    dataset_id = datasets.adapter.find_dataset_id(url=url)
    # Assert
    assert dataset_id == "my-dataset"


def test_find_dataset_id_from_url_if_ends(datasets):
    # Arrange
    url = "https://ny-domain.net/explore/dataset/my-dataset"
    # Act
    datasets.set_adapter(platform_type="opendatasoft")
    dataset_id = datasets.adapter.find_dataset_id(url=url)
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
