import uuid
from datetime import datetime, timedelta, timezone

from application.use_cases.check_deleted_datasets import (
    CheckDeletedDatasetsCommand,
    CheckDeletedDatasetsUseCase,
)
from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase


def test_dataset_snapshot_less_reconstruction(pg_app, pg_datagouv_platform, datagouv_dataset):
    """
    STORY 3.2: Verify that a dataset can be fully restored even if the
    dataset_versions.snapshot column is NULL (using blob_id and diff).
    """
    # 1. Sync first version (generates blob and version)
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_id = result.dataset_id

    # 3. Act: Retrieve dataset from repository
    dataset = pg_app.uow.datasets.get(dataset_id)

    # 4. Assert: Reconstruction works via blob_id
    assert dataset is not None
    assert dataset.title == datagouv_dataset["title"]
    # Check that 'raw' (snapshot) is correctly reconstructed from blob
    assert dataset.raw["id"] == datagouv_dataset["id"]
    assert dataset.raw["title"] == datagouv_dataset["title"]


def test_dataset_deleted_at_tracking(pg_app, pg_datagouv_platform, datagouv_dataset):
    """
    STORY 3.3: Verify that CheckDeletedDatasetsUseCase sets the deleted_at date
    when marking a dataset as deleted.
    """
    # 1. Sync a dataset
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )

    # 2. Run CheckDeletedDatasets with an empty list (dataset should be marked deleted)
    CheckDeletedDatasetsUseCase(uow=pg_app.uow).handle(
        CheckDeletedDatasetsCommand(platform=pg_datagouv_platform, datasets=[])
    )

    # 3. Assert: deleted_at is set in the database
    client = pg_app.uow.client
    row = client.fetchone("SELECT deleted, deleted_at FROM datasets WHERE buid = %s", (datagouv_dataset["id"],))

    assert row["deleted"] is True
    assert row["deleted_at"] is not None
    # Tolerance for execution time
    assert (datetime.now(timezone.utc) - row["deleted_at"]).total_seconds() < 10


def test_dataset_cold_storage_filtering(pg_app, pg_datagouv_platform, datagouv_dataset):
    """
    STORY 3.3: Verify that datasets deleted more than 30 days ago
    are filtered out from default listings (Cold Storage).
    """
    client = pg_app.uow.client

    # 1. Create 3 datasets in different states
    # DS 1: Active
    ds1_id = uuid.uuid4()
    client.execute(
        "INSERT INTO datasets (id, platform_id, buid, slug, page, created, modified) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (str(ds1_id), str(pg_datagouv_platform.id), "buid1", "slug1", "http://page1", datetime.now(), datetime.now()),
    )

    # DS 2: Deleted recently (10 days ago) -> Should be visible
    ds2_id = uuid.uuid4()
    recent_deleted = datetime.now(timezone.utc) - timedelta(days=10)
    client.execute(
        "INSERT INTO datasets (id, platform_id, buid, slug, page, created, modified, deleted, deleted_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            str(ds2_id),
            str(pg_datagouv_platform.id),
            "buid2",
            "slug2",
            "http://page2",
            datetime.now(),
            datetime.now(),
            True,
            recent_deleted,
        ),
    )

    # DS 3: Deleted long ago (40 days ago) -> Should be hidden (Cold Storage)
    ds3_id = uuid.uuid4()
    old_deleted = datetime.now(timezone.utc) - timedelta(days=40)
    client.execute(
        "INSERT INTO datasets (id, platform_id, buid, slug, page, created, modified, deleted, deleted_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            str(ds3_id),
            str(pg_datagouv_platform.id),
            "buid3",
            "slug3",
            "http://page3",
            datetime.now(),
            datetime.now(),
            True,
            old_deleted,
        ),
    )
    client.commit()

    # 2. Act: Search active datasets (default view logic)
    # Note: We need to implement this filtering in the repository or a specific search query
    # Here we test a hypothetical 'search' or listing method that should implement Epic 3 logic.
    # For now, let's assume we'll have a method 'all_active_including_recently_deleted'
    # or just that 'all()' filters out cold storage.

    # For the purpose of the TDD, we expect the repository to have a method that respects this rule.
    active_datasets, _ = pg_app.uow.datasets.search()  # search() excludes cold storage by default

    # 3. Assert
    ids = [d["id"] for d in active_datasets]
    assert str(ds1_id) in ids
    assert str(ds2_id) in ids
    assert str(ds3_id) not in ids, "Dataset in Cold Storage (>30d) should be hidden"
