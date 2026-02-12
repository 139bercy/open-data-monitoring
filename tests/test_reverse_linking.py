from datetime import datetime, timezone
from uuid import uuid4

from application.services.dataset import DatasetMonitoring
from domain.datasets.aggregate import Dataset
from infrastructure.repositories.datasets.in_memory import InMemoryDatasetRepository


def test_reverse_linking_logic():
    # Setup repository with a list for DB
    db = []
    repo = InMemoryDatasetRepository(db=db)
    service = DatasetMonitoring(repository=repo)

    # 1. Create ODS dataset
    ods_platform_id = uuid4()
    now = datetime.now(timezone.utc)
    ods_dataset = Dataset(
        id=uuid4(),
        platform_id=ods_platform_id,
        buid="ods-buid",
        slug="my-ods-slug",
        title="ODS Dataset",
        page="https://data.economie.gouv.fr/explore/dataset/my-ods-slug/information/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
    )
    repo.add(ods_dataset)

    # 2. Create DataGouv dataset with harvest info pointing to ODS
    dg_platform_id = uuid4()
    dg_dataset = Dataset(
        id=uuid4(),
        platform_id=dg_platform_id,
        buid="dg-buid",
        slug="my-dg-slug",
        title="DG Dataset",
        page="https://www.data.gouv.fr/datasets/my-dg-slug/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={"harvest": {"uri": "https://data.economie.gouv.fr/explore/dataset/my-ods-slug/"}},
    )
    repo.add(dg_dataset)

    # Verify slugs are correct in repo
    assert repo.get_id_by_slug_globally("my-ods-slug") == ods_dataset.id
    assert repo.get_id_by_slug_globally("my-dg-slug") == dg_dataset.id

    # 3. Trigger linking for DataGouv dataset
    service.link_datasets(dg_dataset.id)

    # 4. Verify ODS dataset now points to DataGouv
    updated_ods = repo.get(ods_dataset.id)
    assert str(updated_ods.linked_dataset_id) == str(dg_dataset.id)

    # 5. Verify DataGouv dataset also points to ODS (Bidirectional)
    updated_dg = repo.get(dg_dataset.id)
    assert str(updated_dg.linked_dataset_id) == str(ods_dataset.id)

    print("\n✅ Bidirectional linking verified (Reverse scenario)!")


def test_direct_linking_logic():
    # Setup repository
    db = []
    repo = InMemoryDatasetRepository(db=db)
    service = DatasetMonitoring(repository=repo)

    # 1. Create DataGouv dataset (target)
    dg_platform_id = uuid4()
    now = datetime.now(timezone.utc)
    dg_dataset = Dataset(
        id=uuid4(),
        platform_id=dg_platform_id,
        buid="dg-buid",
        slug="my-dg-slug",
        title="DG Dataset",
        page="https://www.data.gouv.fr/datasets/my-dg-slug/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
    )
    repo.add(dg_dataset)

    # 2. Create ODS dataset with source pointing to DataGouv
    ods_platform_id = uuid4()
    ods_dataset = Dataset(
        id=uuid4(),
        platform_id=ods_platform_id,
        buid="ods-buid",
        slug="my-ods-slug",
        title="ODS Dataset",
        page="https://data.economie.gouv.fr/explore/dataset/my-ods-slug/information/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={"metadata": {"default": {"source": "https://www.data.gouv.fr/fr/datasets/my-dg-slug/"}}},
    )
    repo.add(ods_dataset)

    # 3. Trigger linking for ODS dataset
    service.link_datasets(ods_dataset.id)

    # 4. Verify ODS dataset now points to DataGouv
    updated_ods = repo.get(ods_dataset.id)
    assert str(updated_ods.linked_dataset_id) == str(dg_dataset.id)

    # 5. Verify DataGouv dataset also points to ODS (Bidirectional)
    updated_dg = repo.get(dg_dataset.id)
    assert str(updated_dg.linked_dataset_id) == str(ods_dataset.id)

    print("\n✅ Bidirectional linking verified (Direct scenario)!")


def test_volatile_fields_stripping():
    from infrastructure.repositories.datasets.postgres import strip_volatile_fields

    # Create sample raw data with volatile fields
    raw_data = {
        "title": "Test Dataset",
        "harvest": {
            "uri": "https://example.com/dataset",
            "last_update": "2023-01-01T12:00:00Z",
            "modified_at": "2023-01-02T12:00:00Z",
            "remote_id": "12345",
        },
        "resources": [
            {
                "title": "Resource 1",
                "last_modified": "2023-01-01T12:00:00Z",
                "harvest": {"last_update": "2023-01-01T12:00:00Z", "url": "https://example.com/resource"},
                "extras": {
                    "analysis:check_id": 41111791,
                    "analysis:checksum": "abcde",
                    "check:available": True,
                    "check:status": 200,
                    "other:key": "preserve_me",
                },
            }
        ],
    }

    stripped, volatile = strip_volatile_fields(raw_data)

    # Verify harvest fields
    assert "harvest" in stripped
    assert "uri" in stripped["harvest"], "harvest.uri should be preserved"
    assert "remote_id" in stripped["harvest"], "harvest.remote_id should be preserved"
    assert "last_update" not in stripped["harvest"], "harvest.last_update should be stripped"
    assert "modified_at" not in stripped["harvest"], "harvest.modified_at should be stripped"

    # Verify resources fields
    assert len(stripped["resources"]) == 1
    res = stripped["resources"][0]
    assert "last_modified" not in res, "resource.last_modified should be stripped"
    assert "harvest" in res
    assert "url" in res["harvest"], "resource.harvest.url should be preserved"
    assert "last_update" not in res["harvest"], "resource.harvest.last_update should be stripped"

    # Verify extras fields
    assert "extras" in res
    assert "other:key" in res["extras"], "extras.other:key should be preserved"
    assert "analysis:check_id" not in res["extras"], "extras.analysis:check_id should be stripped"
    assert "check:available" not in res["extras"], "extras.check:available should be stripped"

    print("\n✅ Volatile fields stripping verified!")


def test_loose_search_linking():
    # Setup repository
    db = []
    repo = InMemoryDatasetRepository(db=db)
    service = DatasetMonitoring(repository=repo)

    # 1. Create DataGouv dataset (target)
    dg_platform_id = uuid4()
    now = datetime.now(timezone.utc)
    slug = "shared-slug"

    dg_dataset = Dataset(
        id=uuid4(),
        platform_id=dg_platform_id,
        buid="dg-buid-loose",
        slug=slug,
        title="DG Dataset Loose",
        page=f"https://www.data.gouv.fr/datasets/{slug}/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},
    )
    repo.add(dg_dataset)

    # 2. Create ODS dataset with SAME slug but NO explicit link
    ods_platform_id = uuid4()
    ods_dataset = Dataset(
        id=uuid4(),
        platform_id=ods_platform_id,
        buid="ods-buid-loose",
        slug=slug,
        title="ODS Dataset Loose",
        page=f"https://data.economie.gouv.fr/explore/dataset/{slug}/information/",
        created=now,
        modified=now,
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={},  # No metadata source/references
    )
    repo.add(ods_dataset)

    # 3. Trigger linking for ODS dataset
    service.link_datasets(ods_dataset.id)

    # 4. Verify linking (Bidirectional)
    updated_ods = repo.get(ods_dataset.id)
    updated_dg = repo.get(dg_dataset.id)

    assert str(updated_ods.linked_dataset_id) == str(dg_dataset.id)
    assert str(updated_dg.linked_dataset_id) == str(ods_dataset.id)

    print("\n✅ Loose search linking verified!")
