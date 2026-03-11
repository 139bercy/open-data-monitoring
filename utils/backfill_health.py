import asyncio
import os
import sys
from datetime import datetime

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.repositories.datasets.postgres import _calculate_health_scores
from src.settings import app


async def backfill_health_scores():
    print("Starting corrected health score backfill (COMMIT ENABLED)...")
    repo = app.dataset.repository

    # Get all datasets with their quality info
    rows = repo.client.fetchall("""
        SELECT d.id, d.slug, d.modified, d.restricted, d.published,
               dq.has_description, dq.is_slug_valid, dq.syntax_change_score, dq.evaluated_blob_id,
               lv.blob_id as current_blob_id, lv.views_count, lv.api_calls_count, lv.reuses_count, lv.timestamp,
               db.data as raw_data
        FROM datasets d
        LEFT JOIN dataset_quality dq ON d.id = dq.dataset_id
        LEFT JOIN (
            SELECT DISTINCT ON (dataset_id) dataset_id, blob_id, views_count, api_calls_count, reuses_count, timestamp
            FROM dataset_versions
            ORDER BY dataset_id, timestamp DESC
        ) lv ON d.id = lv.dataset_id
        LEFT JOIN dataset_blobs db ON lv.blob_id = db.id
    """)

    total = len(rows)
    print(f"Found {total} datasets to process")

    count = 0
    for i, r in enumerate(rows):
        if i % 100 == 0:
            print(f"Progress: {i}/{total}")

        scores = None
        if r.get("modified") and not r.get("restricted") and r.get("published") is not False:
            scores = _calculate_health_scores(
                {
                    "slug": r.get("slug"),
                    "quality": {
                        "has_description": r.get("has_description") or False,
                        "is_slug_valid": r.get("is_slug_valid") if r.get("is_slug_valid") is not None else True,
                        "syntax_change_score": r.get("syntax_change_score"),
                    },
                    "evaluated_blob_id": r.get("evaluated_blob_id"),
                    "current_blob_id": r.get("current_blob_id"),
                    "modified": r.get("modified"),
                    "views_count": r.get("views_count"),
                    "api_calls_count": r.get("api_calls_count"),
                    "reuses_count": r.get("reuses_count"),
                    "data": r.get("raw_data") or {},
                }
            )

        if scores:
            repo.client.execute(
                """
                INSERT INTO dataset_quality (
                    dataset_id, timestamp, has_description, is_slug_valid,
                    syntax_change_score, evaluated_blob_id,
                    health_score, health_quality_score, health_freshness_score, health_engagement_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dataset_id) DO UPDATE SET
                    health_score = EXCLUDED.health_score,
                    health_quality_score = EXCLUDED.health_quality_score,
                    health_freshness_score = EXCLUDED.health_freshness_score,
                    health_engagement_score = EXCLUDED.health_engagement_score,
                    has_description = EXCLUDED.has_description,
                    is_slug_valid = EXCLUDED.is_slug_valid,
                    syntax_change_score = EXCLUDED.syntax_change_score,
                    evaluated_blob_id = EXCLUDED.evaluated_blob_id
            """,
                (
                    str(r["id"]),
                    r.get("timestamp") or r.get("modified") or datetime.now(),
                    r.get("has_description") or False,
                    r.get("is_slug_valid") if r.get("is_slug_valid") is not None else True,
                    r.get("syntax_change_score"),
                    r.get("evaluated_blob_id"),
                    scores["global"],
                    scores["quality"],
                    scores["freshness"],
                    scores["engagement"],
                ),
            )
            count += 1
            if count % 100 == 0:
                repo.client.commit()

    repo.client.commit()
    print(f"Backfill complete! {count} datasets updated.")


if __name__ == "__main__":
    asyncio.run(backfill_health_scores())
