from uuid import UUID

from application.services.datasets import DatasetsMonitoring
from infrastructure.factories.dataset import DatasetAdapterFactory


def test_create_opendatasoft_dataset(ods_dataset):
    app = DatasetsMonitoring(factory=DatasetAdapterFactory)
    result = app.create_dataset("opendatasoft", **ods_dataset)
    assert isinstance(result, UUID)


def test_create_datagouv_dataset(datagouv_dataset):
    app = DatasetsMonitoring(factory=DatasetAdapterFactory)
    result = app.create_dataset("datagouvfr", **datagouv_dataset)
    assert isinstance(result, UUID)
