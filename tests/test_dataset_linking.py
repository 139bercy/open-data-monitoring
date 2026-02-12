from datetime import datetime
from uuid import uuid4

from domain.datasets.aggregate import Dataset


def create_dataset(raw_meta):
    return Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test-buid",
        slug="test-slug",
        title="Test Title",
        page="https://example.com",
        created=datetime.now(),
        modified=datetime.now(),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw=raw_meta,
    )


def test_extract_external_link_slug_ods_to_datagouv():
    # Arrange
    ds = create_dataset({"metadata": {"default": {"source": "https://www.data.gouv.fr/fr/datasets/target-slug/"}}})

    # Act & Assert
    assert ds.extract_external_link_slug() == "target-slug"


def test_extract_external_link_slug_ods_v1_to_datagouv():
    # Arrange
    ds = create_dataset({"metas": {"default": {"source": "https://www.data.gouv.fr/fr/datasets/target-slug-v1/"}}})

    # Act & Assert
    assert ds.extract_external_link_slug() == "target-slug-v1"


def test_extract_external_link_slug_datagouv_to_ods():
    # Arrange
    ds = create_dataset({"harvest": {"remote_url": "https://data.example.com/explore/dataset/target-ods-slug/"}})

    # Act & Assert
    assert ds.extract_external_link_slug() == "target-ods-slug"


def test_extract_external_link_slug_datagouv_harvest_uri():
    # Arrange
    ds = create_dataset({"harvest": {"uri": "https://data.example.com/explore/dataset/target-via-uri/"}})

    # Act & Assert
    assert ds.extract_external_link_slug() == "target-via-uri"


def test_extract_external_link_slug_no_link():
    # Arrange
    ds = create_dataset({"metadata": {"default": {"source": "https://google.com"}}})

    # Act & Assert
    assert ds.extract_external_link_slug() is None


def test_extract_external_link_slug_datagouv_description_fallback():
    # Arrange
    ds = create_dataset(
        {
            "description": "Ce jeu de données est moissonné depuis https://data.economie.gouv.fr/explore/dataset/target-from-desc/ permettant sa mise à jour."
        }
    )

    # Act & Assert
    assert ds.extract_external_link_slug() == "target-from-desc"
