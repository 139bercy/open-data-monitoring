from application.dtos.dataset import DatasetDTO
from infrastructure.adapters.datasets.datagouvfr import DatagouvDatasetAdapter


def test_datagouv_adapter_map_archived_dataset():
    # Arrange
    adapter = DatagouvDatasetAdapter()
    raw_data = {
        "id": "84348666-8b45-49c7-9de0-52b127314233",
        "slug": "frontieres-mondiales",
        "page": "https://www.data.gouv.fr/datasets/frontieres-mondiales/",
        "created_at": "2020-01-01T00:00:00+00:00",
        "last_update": "2024-01-01T00:00:00+00:00",
        "contact_points": [{"role": "publisher", "name": "MEFSIN"}],
        "archived": "2026-03-10T15:00:00.000000+00:00",
        "metrics": {"resources_downloads": 100, "views": 200, "reuses": 5, "followers": 10},
        "description": "Dataset description",
        "title": "Frontières mondiales",
        "private": False,
    }

    # Act
    dto = adapter.map(**raw_data)

    # Assert
    assert isinstance(dto, DatasetDTO)
    assert dto.restricted is True
    assert dto.published is True


def test_datagouv_adapter_map_active_dataset():
    # Arrange
    adapter = DatagouvDatasetAdapter()
    raw_data = {
        "id": "active-dataset-id",
        "slug": "active-dataset",
        "page": "https://www.data.gouv.fr/datasets/active-dataset/",
        "created_at": "2020-01-01T00:00:00+00:00",
        "last_update": "2024-01-01T00:00:00+00:00",
        "contact_points": [{"role": "publisher", "name": "MEFSIN"}],
        "archived": None,
        "metrics": {"resources_downloads": 100, "views": 200, "reuses": 5, "followers": 10},
        "description": "Dataset description",
        "title": "Active Dataset",
        "private": False,
    }

    # Act
    dto = adapter.map(**raw_data)

    # Assert
    assert isinstance(dto, DatasetDTO)
    assert dto.restricted is False
    assert dto.published is True


def test_datagouv_adapter_map_private_dataset():
    # Arrange
    adapter = DatagouvDatasetAdapter()
    raw_data = {"id": "private-dataset-id", "slug": "private-dataset", "archived": None, "private": True}

    # Act
    dto = adapter.map(**raw_data)

    # Assert
    assert dto.restricted is False
    assert dto.published is False


def test_datagouv_adapter_map_missing_fields_no_crash():
    # Arrange
    adapter = DatagouvDatasetAdapter()
    raw_data = {"id": "minimal-id", "slug": "minimal-slug"}

    # Act & Assert
    dto = adapter.map(**raw_data)
    assert dto.buid == "minimal-id"
    assert dto.published is True
    assert dto.restricted is False
