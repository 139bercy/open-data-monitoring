import hashlib
import json

import pytest

from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase
from infrastructure.repositories.datasets.postgres import strip_volatile_fields


def test_strip_volatile_fields_datagouv():
    # Arrange
    snapshot = {
        "id": "test_dg",
        "title": "DG Dataset",
        "metrics": {"views": 100, "downloads": 50},
        "last_modified": "2024-01-01T12:00:00Z",
        "internal": {"created_at_internal": "2024-01-01T12:00:00Z", "last_modified_internal": "2024-01-01T12:00:00Z"},
        "resources": [
            {
                "id": "res1",
                "metrics": {"downloads": 10},
                "extras": {"check:date": "2024-01-01", "analysis:parsing:status": "done", "stable_field": "keep_me"},
            }
        ],
    }

    # Act
    stripped, volatile = strip_volatile_fields(snapshot)

    # Assert
    assert "metrics" in stripped
    assert "views" not in stripped["metrics"]
    assert "reuses_by_months" not in stripped["metrics"]
    assert "last_modified" not in stripped
    assert "last_modified_internal" not in stripped["internal"]
    assert stripped["internal"]["created_at_internal"] == "2024-01-01T12:00:00Z"
    assert stripped["internal"]["created_at_internal"] == "2024-01-01T12:00:00Z"

    # Resources: granular stripping
    assert "resources" in stripped
    res = stripped["resources"][0]
    assert "check:date" not in res["extras"]
    assert "analysis:parsing:status" not in res["extras"]
    assert res["extras"]["stable_field"] == "keep_me"


def test_hashing_stability():

    # Arrange: DataGouv style snapshots
    # s1 and s2 have different volatile fields (views, time-series, timestamps, resources)
    # but same static metadata (id, title)
    s1 = {
        "id": "dg1",
        "title": "Static Title",
        "metrics": {"views": 100, "reuses_by_months": {"2024-01": 1}},
        "last_modified": "2024-01-01T12:00:00Z",
        "internal": {"last_modified_internal": "2024-01-01T12:00:00Z", "created_at_internal": "2020-01-01"},
        "resources": [{"id": "r1", "last_modified": "2024-01-01"}],
    }

    s2 = {
        "id": "dg1",
        "title": "Static Title",
        "metrics": {
            "views": 100,  # Stable metrics should remain
            "reuses_by_months": {"2024-01": 5},  # Diff in time-series
        },
        "last_modified": "2024-01-02T12:00:00Z",  # Diff in timestamp
        "internal": {"last_modified_internal": "2024-01-02T12:00:00Z", "created_at_internal": "2020-01-01"},
        "resources": [{"id": "r1", "last_modified": "2024-01-02"}],  # resources will be stripped
    }

    # Act
    h1 = hashlib.sha256(json.dumps(strip_volatile_fields(s1)[0], sort_keys=True).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(strip_volatile_fields(s2)[0], sort_keys=True).encode()).hexdigest()

    # Assert
    assert h1 == h2

    # Verify we didn't strip too much
    stripped, _ = strip_volatile_fields(s1)
    assert stripped["id"] == "dg1"
    assert stripped["title"] == "Static Title"
    assert "views" not in stripped["metrics"]
    assert "reuses_by_months" not in stripped["metrics"]


def test_postgresql_deduplication(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange
    # First sync: create first version and blob
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_1_id = result.dataset_id

    # Act
    # Second sync: change ONLY volatile fields that are stripped (last_modified, time-series)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["metrics"] = datagouv_dataset_v2["metrics"].copy()
    datagouv_dataset_v2["metrics"]["reuses_by_months"] = {"2024-02": 10}
    # For DataGouv, 'last_update' maps to 'modified' which is in the domain checksum
    datagouv_dataset_v2["last_update"] = "2024-02-01T12:00:00Z"

    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v2["id"], raw_data=datagouv_dataset_v2
        )
    )

    # Assert
    client = pg_app.uow.client
    versions = client.fetchall("SELECT * FROM dataset_versions WHERE dataset_id = %s", (str(dataset_1_id),))
    blobs = client.fetchall("SELECT * FROM dataset_blobs")

    assert len(versions) == 1, "Should NOT create a new version as only volatile/technical fields changed"
    assert len(blobs) == 1

    # Act 2: Third sync: change a CORE metric (views)
    # But FIRST, we must bypass the 12h cooldown by aging the first version
    client.execute(
        "UPDATE dataset_versions SET timestamp = timestamp - interval '13 hours' WHERE dataset_id = %s",
        (str(dataset_1_id),),
    )

    datagouv_dataset_v3 = datagouv_dataset_v2.copy()
    datagouv_dataset_v3["metrics"] = datagouv_dataset_v3["metrics"].copy()
    datagouv_dataset_v3["metrics"]["views"] += 100

    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v3["id"], raw_data=datagouv_dataset_v3
        )
    )

    # Assert 2
    versions_final = client.fetchall(
        "SELECT * FROM dataset_versions WHERE dataset_id = %s ORDER BY timestamp ASC", (str(dataset_1_id),)
    )
    assert len(versions_final) == 2, "Should create a new version when a core metric changes"
    assert versions_final[1]["views_count"] == datagouv_dataset_v3["metrics"]["views"]


def test_postgresql_reconstruction(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange: Add some volatile fields that should be stripped then reconstructed
    datagouv_dataset["harvest"] = {"last_id": "123", "status": "ok", "last_update": "2024-01-01T12:00:00Z"}
    datagouv_dataset["metrics"]["reuses_by_months"] = {"2024-01": 5}
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_id = result.dataset_id

    # Act
    # Get the dataset back from repository
    dataset = pg_app.dataset.repository.get(dataset_id)

    # Assert
    assert len(dataset.versions) == 1
    version = dataset.versions[0]
    # Check that volatile counts are still preserved in the explicit columns
    assert version.views_count == datagouv_dataset["metrics"]["views"]
    assert version.reuses_count == datagouv_dataset["metrics"]["reuses"]

    # Check bit-perfect reconstruction of the snapshot
    assert "harvest" in version.snapshot
    assert version.snapshot["harvest"]["last_id"] == "123"
    assert version.snapshot["metrics"]["reuses_by_months"] == {"2024-01": 5}

    # The blob stored in DB should NOT have these fields
    client = pg_app.uow.client
    blob = client.fetchone("SELECT data FROM dataset_blobs LIMIT 1")["data"]
    assert "last_update" not in blob
    assert "reuses_by_months" not in blob["metrics"]


def test_version_diff_tracking(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_1_id = result.dataset_id

    # Act: Second sync with a title change AND modified change (structural)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["title"] = "Updated Title"
    datagouv_dataset_v2["last_update"] = "2026-01-01T12:00:00Z"
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v2["id"], raw_data=datagouv_dataset_v2
        )
    )

    # Assert
    dataset = pg_app.dataset.repository.get(dataset_1_id)
    assert len(dataset.versions) == 2

    # Version 1 should have no diff (first version)
    assert dataset.versions[0].diff is None

    # Version 2 should have a diff showing the title change
    v2 = dataset.versions[1]
    assert v2.diff is not None
    assert v2.diff["title"]["_t"] == "changed"
    assert v2.diff["title"]["new"] == "Updated Title"
    assert v2.diff["title"]["old"] == datagouv_dataset["title"]

    # Act 2: Third sync with only a metric change
    # Bypass cooldown
    client = pg_app.uow.client
    client.execute(
        "UPDATE dataset_versions SET timestamp = timestamp - interval '13 hours' WHERE dataset_id = %s",
        (str(dataset_1_id),),
    )

    datagouv_dataset_v3 = datagouv_dataset_v2.copy()
    datagouv_dataset_v3["metrics"]["views"] = 20000
    datagouv_dataset_v3["last_update"] = "2026-01-01T13:00:00Z"  # Technical change, won't trigger version on its own
    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v3["id"], raw_data=datagouv_dataset_v3
        )
    )

    # Assert 2
    dataset = pg_app.dataset.repository.get(dataset_1_id)
    assert len(dataset.versions) == 3
    v3 = dataset.versions[2]
    assert v3.diff is not None
    # The diff should show the view change
    assert "views_count" in v3.diff
    assert v3.diff["views_count"]["new"] == 20000


@pytest.mark.skip(reason="Cooldown is disabled (hours=0) for now")
def test_versioning_cooldown_noise_reduction(pg_app, pg_datagouv_platform, datagouv_dataset):
    # 1. First sync
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset["id"], raw_data=datagouv_dataset
        )
    )
    dataset_id = result.dataset_id
    ds = pg_app.dataset.repository.get(dataset_id)
    assert len(ds.versions) == 1

    # 2. Second sync with ONLY metric change (within seconds -> cooldown active)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["metrics"]["views"] = (datagouv_dataset.get("metrics", {}).get("views") or 0) + 1

    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v2["id"], raw_data=datagouv_dataset_v2
        )
    )

    # ASSERT: Still only 1 version because of 24h cooldown
    ds_after = pg_app.dataset.repository.get(dataset_id)
    assert len(ds_after.versions) == 1, "Should NOT create a new version for minor metric change within 24h"

    # 3. Third sync with STRUCTURAL change (cooldown ignored)
    datagouv_dataset_v3 = datagouv_dataset_v2.copy()
    # Change a field that is ACTUALLY in the checksum
    # For DataGouv, 'last_update' is mapped to 'modified'
    datagouv_dataset_v3["last_update"] = "2025-01-01T12:00:00"

    SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(
            platform=pg_datagouv_platform, platform_dataset_id=datagouv_dataset_v3["id"], raw_data=datagouv_dataset_v3
        )
    )

    # ASSERT: 2 versions (Initial + Structural)
    ds_final = pg_app.dataset.repository.get(dataset_id)
    assert len(ds_final.versions) == 2, "Should create a new version on structural change regardless of cooldown"
