import hashlib
import json

import pytest
from psycopg2._json import Json

from application.handlers import upsert_dataset
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
    import hashlib

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
    dataset_1_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)

    # Act
    # Second sync: change ONLY volatile fields that are stripped (last_modified, time-series)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["metrics"] = datagouv_dataset_v2["metrics"].copy()
    datagouv_dataset_v2["metrics"]["reuses_by_months"] = {"2024-02": 10}
    # For DataGouv, 'last_update' maps to 'modified' which is in the domain checksum
    datagouv_dataset_v2["last_update"] = "2024-02-01T12:00:00Z"

    upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset_v2)

    # Assert
    client = pg_app.uow.client
    versions = client.fetchall("SELECT * FROM dataset_versions WHERE dataset_id = %s", (str(dataset_1_id),))
    blobs = client.fetchall("SELECT * FROM dataset_blobs")

    assert len(versions) == 2
    assert len(blobs) == 1, "Only one blob should exist as only volatile fields changed"
    assert versions[0]["blob_id"] == versions[1]["blob_id"]


def test_postgresql_reconstruction(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange: Add some volatile fields that should be stripped then reconstructed
    datagouv_dataset["harvest"] = {"last_id": "123", "status": "ok", "last_update": "2024-01-01T12:00:00Z"}
    datagouv_dataset["metrics"]["reuses_by_months"] = {"2024-01": 5}
    dataset_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)

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


def test_postgresql_legacy_compatibility(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange: Manually insert a legacy version with snapshot but no blob_id
    dataset_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)
    client = pg_app.uow.client

    # Clear auto-created version and insert a legacy one
    client.execute("DELETE FROM dataset_versions")
    client.execute("DELETE FROM dataset_blobs")

    client.execute(
        "INSERT INTO dataset_versions (dataset_id, snapshot, checksum, downloads_count) VALUES (%s, %s, %s, %s)",
        (str(dataset_id), Json(datagouv_dataset), "legacy_checksum", 10),
    )

    # Act
    dataset = pg_app.dataset.repository.get(dataset_id)

    # Assert
    assert len(dataset.versions) == 1
    version = dataset.versions[0]
    assert version.snapshot["id"] == datagouv_dataset["id"]
    assert version.downloads_count == 10


def test_migration_logic(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange: Manually insert multiple legacy versions
    dataset_1_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)
    client = pg_app.uow.client
    client.execute("DELETE FROM dataset_versions")
    client.execute("DELETE FROM dataset_blobs")

    # v1
    client.execute(
        "INSERT INTO dataset_versions (dataset_id, snapshot, checksum, downloads_count) VALUES (%s, %s, %s, %s)",
        (str(dataset_1_id), Json(datagouv_dataset), "c1", 10),
    )
    # v2 (same content, different metrics)
    v2_data = datagouv_dataset.copy()
    v2_data["metrics"] = v2_data["metrics"].copy()
    v2_data["metrics"]["reuses_by_months"] = {"2024-02": 10}
    client.execute(
        "INSERT INTO dataset_versions (dataset_id, snapshot, checksum, downloads_count) VALUES (%s, %s, %s, %s)",
        (str(dataset_1_id), Json(v2_data), "c2", 20),
    )

    # Act: Run mini-migration logic on the SAME connection to avoid deadlocks
    # Fetch legacy versions
    versions = client.fetchall("""
        SELECT id, dataset_id, snapshot, downloads_count, api_calls_count,
               views_count, reuses_count, followers_count, popularity_score
        FROM dataset_versions
        WHERE snapshot IS NOT NULL
    """)
    for v in versions:
        snapshot = v["snapshot"]
        stripped, _ = strip_volatile_fields(snapshot)
        stable_hash = hashlib.sha256(json.dumps(stripped, sort_keys=True).encode()).hexdigest()

        # Upsert blob (Per-dataset)
        blob_id = client.fetchone(
            """
            INSERT INTO dataset_blobs (dataset_id, hash, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_id, hash)
            DO UPDATE SET id = dataset_blobs.id
            RETURNING id
            """,
            (v["dataset_id"], stable_hash, Json(stripped)),
        )["id"]

        # Backfill logic
        downloads = v["downloads_count"]
        if downloads is None:
            # For DataGouv we might fetch from metrics if needed, but here we simulate downloads_count preservation
            downloads = snapshot.get("metrics", {}).get("resources_downloads")

        views = snapshot.get("metrics", {}).get("views")

        # Update version
        client.execute(
            """UPDATE dataset_versions SET
               blob_id = %s, downloads_count = %s, views_count = %s
               WHERE id = %s""",
            (str(blob_id), downloads, views, str(v["id"])),
        )

    # Assert
    versions_after = client.fetchall("SELECT * FROM dataset_versions")
    blobs_after = client.fetchall("SELECT * FROM dataset_blobs")

    assert len(versions_after) == 2
    assert len(blobs_after) == 1, "Migration should have deduplicated the two versions into one blob"
    assert versions_after[0]["blob_id"] is not None
    assert versions_after[0]["blob_id"] == versions_after[1]["blob_id"]


def test_version_diff_tracking(pg_app, pg_datagouv_platform, datagouv_dataset):
    # Arrange
    dataset_1_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)

    # Act: Second sync with a title change AND modified change (structural)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["title"] = "Updated Title"
    datagouv_dataset_v2["last_update"] = "2026-01-01T12:00:00Z"
    upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset_v2)

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
    datagouv_dataset_v3 = datagouv_dataset_v2.copy()
    datagouv_dataset_v3["metrics"]["views"] = 20000
    datagouv_dataset_v3["last_update"] = "2026-01-01T13:00:00Z"  # Structural change!
    upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset_v3)

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
    dataset_id = upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset)
    ds = pg_app.dataset.repository.get(dataset_id)
    assert len(ds.versions) == 1

    # 2. Second sync with ONLY metric change (within seconds -> cooldown active)
    datagouv_dataset_v2 = datagouv_dataset.copy()
    datagouv_dataset_v2["metrics"]["views"] = (datagouv_dataset.get("metrics", {}).get("views") or 0) + 1

    upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset_v2)

    # ASSERT: Still only 1 version because of 24h cooldown
    ds_after = pg_app.dataset.repository.get(dataset_id)
    assert len(ds_after.versions) == 1, "Should NOT create a new version for minor metric change within 24h"

    # 3. Third sync with STRUCTURAL change (cooldown ignored)
    datagouv_dataset_v3 = datagouv_dataset_v2.copy()
    # Change a field that is ACTUALLY in the checksum
    # For DataGouv, 'last_update' is mapped to 'modified'
    datagouv_dataset_v3["last_update"] = "2025-01-01T12:00:00"

    upsert_dataset(pg_app, pg_datagouv_platform, datagouv_dataset_v3)

    # ASSERT: 2 versions (Initial + Structural)
    ds_final = pg_app.dataset.repository.get(dataset_id)
    assert len(ds_final.versions) == 2, "Should create a new version on structural change regardless of cooldown"
