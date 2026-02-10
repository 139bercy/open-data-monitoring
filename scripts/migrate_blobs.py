import hashlib
import json
import os

from dotenv import load_dotenv
from psycopg2._json import Json

from common import calculate_snapshot_diff
from infrastructure.database.postgres import PostgresClient
from infrastructure.repositories.datasets.postgres import strip_volatile_fields


def migrate(db_name=None, db_user=None, db_pass=None, db_host=None, db_port=None):  # noqa: C901
    load_dotenv()

    db_name = db_name or os.getenv("DB_NAME", "odm")
    db_user = db_user or os.getenv("DB_USER", "postgres")
    db_pass = db_pass or os.getenv("DB_PASSWORD", "postgres")
    db_host = db_host or os.getenv("DB_HOST", "localhost")
    db_port = db_port or os.getenv("DB_PORT", "5432")

    # We use two clients: one for streaming (read) and one for updates (write)
    # to avoid "named cursor isn't valid anymore" when committing.
    reader_client = PostgresClient(db_name, db_user, db_pass, db_host, db_port)
    writer_client = PostgresClient(db_name, db_user, db_pass, db_host, db_port)

    print(f"Starting migration on {db_name}: Deduplicating snapshots into dataset_blobs (Smart Hashing)...")

    # 1. Reset migration progress
    print("Resetting existing blob links...")
    writer_client.execute("UPDATE dataset_versions SET blob_id = NULL WHERE blob_id IS NOT NULL")
    writer_client.execute("DELETE FROM dataset_blobs")
    writer_client.commit()

    # 2. Fetch total count for progress reporting
    total_count = writer_client.fetchone("SELECT count(*) as count FROM dataset_versions WHERE snapshot IS NOT NULL")[
        "count"
    ]
    print(f"Found {total_count} versions to migrate.")

    # 3. Stream all versions that have a snapshot
    versions_stream = reader_client.stream_fetchall(
        """
        SELECT dv.id, dv.dataset_id, dv.snapshot, dv.checksum, dv.downloads_count, dv.api_calls_count,
               dv.views_count, dv.reuses_count, dv.followers_count, dv.popularity_score,
               d.id AS parent_exists
        FROM dataset_versions dv
        LEFT JOIN datasets d ON d.id = dv.dataset_id
        WHERE dv.snapshot IS NOT NULL
        ORDER BY dv.dataset_id, dv.timestamp ASC
    """,
        name="migration_cursor",
    )

    count = 0
    skipped_orphans = 0
    last_comparable_by_dataset = {}
    last_hash_by_dataset = {}
    blob_cache = {}  # (dataset_id, hash) -> blob_id

    with open("migration_orphans.log", "w") as orphan_log:
        for v in versions_stream:
            ds_id = v["dataset_id"]

            if not v["parent_exists"]:
                skipped_orphans += 1
                orphan_log.write(f"Orphan found: version_id={v['id']}, dataset_id={ds_id}\n")
                continue

            snapshot = v["snapshot"]

            # 3. Backfill columns if they are empty
            downloads = v["downloads_count"]
            api_calls = v["api_calls_count"]
            views = v["views_count"]
            reuses = v["reuses_count"]
            followers = v["followers_count"]
            popularity = v["popularity_score"]

            # ODS extraction
            if snapshot.get("asset_type") == "ods_dataset" or "download_count" in snapshot:
                downloads = downloads if downloads is not None else snapshot.get("download_count")
                api_calls = api_calls if api_calls is not None else snapshot.get("api_call_count")
                reuses = reuses if reuses is not None else snapshot.get("reuse_count")
                popularity = popularity if popularity is not None else snapshot.get("popularity_score")
            # DataGouv extraction
            elif "metrics" in snapshot:
                m = snapshot["metrics"]
                downloads = downloads if downloads is not None else m.get("resources_downloads")
                views = views if views is not None else m.get("views")
                reuses = reuses if reuses is not None else m.get("reuses")
                followers = followers if followers is not None else m.get("followers")

            # 4. Strip volatile fields and calculate stable hash
            stripped, volatile = strip_volatile_fields(snapshot)
            data_str = json.dumps(stripped, sort_keys=True)
            stable_hash = hashlib.sha256(data_str.encode()).hexdigest()

            # 4.5 Extract title for persistence (with ODS support)
            title = snapshot.get("title")
            if not title and "metas" in snapshot:
                title = snapshot.get("metas", {}).get("default", {}).get("title")

            if isinstance(title, dict):  # ODS sometimes has {"value": "..."}
                title = title.get("value")

            if not title:
                title = snapshot.get("slug", "Untitled")

            # Construct comparable dict including metrics for the audit log (diff)
            current_comparable = stripped.copy()
            metrics = {
                "downloads_count": downloads,
                "api_calls_count": api_calls,
                "views_count": views,
                "reuses_count": reuses,
                "followers_count": followers,
                "popularity_score": popularity,
            }
            current_comparable.update(metrics)

            # 5. Calculate diff against previous version (with FAST-PATH)
            diff = None
            if ds_id in last_comparable_by_dataset:
                # FAST-PATH: If the stripped data is identical (same hash), only compare metrics
                if ds_id in last_hash_by_dataset and stable_hash == last_hash_by_dataset[ds_id]:
                    prev_metrics = {k: last_comparable_by_dataset[ds_id].get(k) for k in metrics.keys()}
                    if metrics != prev_metrics:
                        diff = {}
                        for k, v_new in metrics.items():
                            v_old = prev_metrics.get(k)
                            if v_old != v_new:
                                diff[k] = {"_t": "changed", "old": v_old, "new": v_new}
                else:
                    # SLOW-PATH: Full recursive diff for structural changes
                    diff = calculate_snapshot_diff(last_comparable_by_dataset[ds_id], current_comparable)

            last_comparable_by_dataset[ds_id] = current_comparable
            last_hash_by_dataset[ds_id] = stable_hash

            # 5. Upsert the blob (Per-dataset deduplication) - with CACHE
            cache_key = (str(ds_id), stable_hash)
            if cache_key in blob_cache:
                blob_id = blob_cache[cache_key]
            else:
                blob_row = writer_client.fetchone(
                    """
                    INSERT INTO dataset_blobs (dataset_id, hash, data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (dataset_id, hash)
                    DO UPDATE SET id = dataset_blobs.id
                    RETURNING id
                    """,
                    (str(ds_id), stable_hash, Json(stripped)),
                )
                blob_id = blob_row["id"]
                blob_cache[cache_key] = blob_id

            # 6. Update the version to point to the blob and ensure counts are kept
            writer_client.execute(
                """UPDATE dataset_versions SET
                   blob_id = %s,
                   downloads_count = %s,
                   api_calls_count = %s,
                   views_count = %s,
                   reuses_count = %s,
                   followers_count = %s,
                   popularity_score = %s,
                   diff = %s,
                   title = %s,
                   metadata_volatile = %s
                   WHERE id = %s""",
                (
                    str(blob_id),
                    downloads,
                    api_calls,
                    views,
                    reuses,
                    followers,
                    popularity,
                    Json(diff) if diff else None,
                    title,
                    Json(volatile) if volatile else None,
                    str(v["id"]),
                ),
            )
            count += 1
            if (count + skipped_orphans) % 1000 == 0:
                print(
                    f"Progress: {(count + skipped_orphans)}/{total_count} ({(count + skipped_orphans) / total_count:.1%}) - Migrated: {count}, Orphans: {skipped_orphans}..."
                )
                writer_client.commit()

    writer_client.commit()
    print(
        f"Migration finished. {count} versions updated, {skipped_orphans} orphans skipped (see migration_orphans.log)."
    )
    reader_client.close()
    writer_client.close()


if __name__ == "__main__":
    migrate()
