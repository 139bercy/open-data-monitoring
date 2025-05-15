from uuid import UUID

from application.services.datasets import DatasetsMonitoring
from infrastructure.factories.dataset import DatasetAdapterFactory


def test_create_opendatasoft_dataset(ods_dataset):
    # Arrange
    app = DatasetsMonitoring(factory=DatasetAdapterFactory)
    # Act
    result = app.create_dataset("opendatasoft", **ods_dataset)
    # Assert
    assert isinstance(result.id, UUID)


def test_create_datagouv_dataset(datagouv_dataset):
    # Arrange
    app = DatasetsMonitoring(factory=DatasetAdapterFactory)
    # Act
    result = app.create_dataset("datagouvfr", **datagouv_dataset)
    # Assert
    assert isinstance(result.id, UUID)
