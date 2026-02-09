import os

from dotenv import load_dotenv

from infrastructure.database.postgres import PostgresClient
from infrastructure.repositories.datasets.postgres import strip_volatile_fields


def verify(sample_size=100):
    load_dotenv()

    db_name = os.getenv("DB_NAME", "odm")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    client = PostgresClient(db_name, db_user, db_pass, db_host, db_port)

    # 1. Fetch a random sample of datasets with migrated blobs
    print(f"Fetching a random sample of {sample_size} datasets for verification...")
    datasets = client.fetchall(
        """
        SELECT d.id, d.buid, d.platform_id, p.type as platform_type, p.name,
               db.data as migrated_blob
        FROM datasets d
        JOIN platforms p ON d.platform_id = p.id
        JOIN (
            SELECT DISTINCT ON (dataset_id) dataset_id, blob_id
            FROM dataset_versions
            WHERE blob_id IS NOT NULL
            ORDER BY dataset_id, timestamp DESC
        ) dv ON d.id = dv.dataset_id
        JOIN dataset_blobs db ON dv.blob_id = db.id
        ORDER BY random()
        LIMIT %s
    """,
        (sample_size,),
    )

    results = {"ok": 0, "mismatch": 0, "error": 0}

    for d in datasets:
        print(f"Verifying {d['platform_type']} dataset: {d['buid']}...")
        try:
            # 2. Re-crawl or Simulate crawl (Using saved snapshot or fresh crawl if possible)
            # Here we compare the migrated blob (stripped) with what a NEW crawl would produce (stripped)

            # For verification, we'll try to find the latest raw snapshot in the DB to avoid network hits
            latest_raw = client.fetchone(
                """
                SELECT snapshot FROM dataset_versions
                WHERE dataset_id = %s AND snapshot IS NOT NULL
                ORDER BY timestamp DESC LIMIT 1
            """,
                (str(d["id"]),),
            )

            if not latest_raw:
                print(f"  [SKIP] No raw snapshot found for {d['buid']}")
                continue

            fresh_stripped, _ = strip_volatile_fields(latest_raw["snapshot"])

            # 3. Compare
            if fresh_stripped == d["migrated_blob"]:
                print("  [OK] Blot matches stripped snapshot.")
                results["ok"] += 1
            else:
                print("  [MISMATCH] Difference detected!")
                results["mismatch"] += 1
                # Optional: print specific diff

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            results["error"] += 1

    print("\nVerification Summary:")
    print(f" - OK: {results['ok']}")
    print(f" - Mismatches: {results['mismatch']}")
    print(f" - Errors: {results['error']}")

    client.close()


if __name__ == "__main__":
    verify()
