import asyncio
import os
import sys
import uuid

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from settings import app


async def backfill_health_scores():
    print("Starting Domain-driven health score backfill...")
    repo = app.dataset.repository

    # Get all dataset IDs
    rows = repo.client.fetchall("SELECT id FROM datasets")
    total = len(rows)
    print(f"Found {total} datasets to process")

    count = 0
    for i, r in enumerate(rows):
        if i > 0 and i % 100 == 0:
            print(f"Progress: {i}/{total}")
            repo.client.commit()

        try:
            dataset_id = uuid.UUID(r["id"])
            # Load dataset (Repo.get fetches quality and identifying metadata)
            dataset = repo.get(dataset_id, include_versions=False)

            if dataset:
                # Triggers domain calculation and persistence to dataset_quality
                repo.add(dataset)
                count += 1
        except Exception as e:
            print(f"Error processing {r['id']}: {e}")

    repo.client.commit()
    # Refresh the analytics view
    repo.client.execute("REFRESH MATERIALIZED VIEW direction_health_stats_view")
    print(f"Backfill complete! {count} datasets updated and view refreshed.")


if __name__ == "__main__":
    asyncio.run(backfill_health_scores())
