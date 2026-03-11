"""
Bulk LLM Semantic Audit Script — Async + Checkpoint
=====================================================
Lance un audit sémantique LLM en asynchrone sur tous les datasets
publiés et non-restreints. Reprend depuis son point d'arrêt si le
script est interrompu.

Usage:
    ./venv/bin/python utils/bulk_llm_audit.py [OPTIONS]

Options:
    --limit N          Max number of datasets to audit
    --skip-evaluated   Skip datasets already with evaluation_results
    --platform SLUG    Filter by platform slug
    --publisher NAME   Filter by publisher name
    --prompt-type TYPE "light" (default) or "stscandard"
    --concurrency N    Max parallel LLM calls (default: 3)
    --dry-run          List eligible datasets without calling LLM
    --reset            Ignore existing checkpoint and restart from scratch
"""

import argparse
import asyncio
import json
import os
import sys
import time

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from application.services.quality_assessment import QualityAssessmentService
from infrastructure.adapters.quality.metadata_mappers import DatagouvMetadataMapper, OpendatasoftMetadataMapper
from infrastructure.database.postgres import PostgresClient
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from infrastructure.unit_of_work import PostgresUnitOfWork
from logger import logger
from settings import app

DCAT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "quality", "dcat_reference.md"))
CHARTER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dev", "docs", "charte-opendatamef.md"))
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".bulk_audit_checkpoint.json")


def _make_service() -> QualityAssessmentService:
    """Create a fresh QualityAssessmentService with its own DB connection.
    Required for thread-safe concurrent execution (psycopg2 is not thread-safe).
    """
    import os as _os

    client = PostgresClient(
        dbname=_os.environ["DB_NAME"],
        user=_os.environ["DB_USER"],
        password=_os.environ["DB_PASSWORD"],
        host="localhost",
        port=int(_os.environ["DB_PORT"]),
    )
    uow = PostgresUnitOfWork(client)
    evaluator = OpenAIEvaluator(model_name="gpt-4o-mini")
    mappers = {
        "opendatasoft": OpendatasoftMetadataMapper(),
        "datagouvfr": DatagouvMetadataMapper(),
    }
    return QualityAssessmentService(evaluator=evaluator, uow=uow, mappers=mappers)


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------


def load_checkpoint() -> set[str]:
    """Load already-processed dataset IDs from the checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE) as f:
                data = json.load(f)
            return set(data.get("done", []))
        except Exception:
            pass
    return set()


def save_checkpoint(done: set[str]) -> None:
    """Persist the set of processed dataset IDs to disk."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"done": list(done)}, f)


def reset_checkpoint() -> None:
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("🗑  Checkpoint supprimé.")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bulk async LLM semantic audit for published, non-restricted datasets."
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-evaluated", action="store_true")
    parser.add_argument("--platform", type=str, default=None)
    parser.add_argument("--publisher", type=str, default=None)
    parser.add_argument("--prompt-type", type=str, default="standard", choices=["light", "standard"])
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Dataset fetching
# ---------------------------------------------------------------------------


def fetch_datasets(args) -> list[dict]:
    """Query published, non-restricted datasets from the repository."""
    repo = app.dataset.repository

    rows = repo.client.fetchall(
        """
        SELECT d.id, d.slug, d.publisher, p.slug as platform_slug,
               (dq.evaluation_results IS NOT NULL) as already_evaluated
        FROM datasets d
        JOIN platforms p ON d.platform_id = p.id
        LEFT JOIN (
            SELECT DISTINCT ON (dataset_id) dataset_id, evaluation_results
            FROM dataset_quality
            ORDER BY dataset_id, timestamp DESC
        ) dq ON d.id = dq.dataset_id
        WHERE d.published IS TRUE
          AND d.restricted IS NOT TRUE
          AND d.deleted IS NOT TRUE
          {platform_filter}
          {publisher_filter}
        ORDER BY d.modified DESC
        {limit_clause}
        """.format(
            platform_filter="AND p.slug = %(platform)s" if args.platform else "",
            publisher_filter="AND d.publisher = %(publisher)s" if args.publisher else "",
            limit_clause=f"LIMIT {args.limit}" if args.limit else "",
        ),
        {
            **({"platform": args.platform} if args.platform else {}),
            **({"publisher": args.publisher} if args.publisher else {}),
        },
    )
    return rows


# ---------------------------------------------------------------------------
# Core async logic
# ---------------------------------------------------------------------------


async def audit_one(
    row: dict,
    semaphore: asyncio.Semaphore,
    prompt_type: str,
    done: set[str],
    lock: asyncio.Lock,
    counters: dict,
) -> None:
    """Audit a single dataset, creating a dedicated DB connection per call."""
    dataset_id = str(row["id"])
    slug = row["slug"]

    async with semaphore:
        try:
            t0 = time.time()
            # Run the synchronous (blocking) LLM call in a thread pool.
            # Each call creates its own DB connection — psycopg2 is not thread-safe.
            def _run():
                service = _make_service()
                return service.evaluate_dataset(
                    dataset_id=dataset_id,
                    dcat_path=DCAT_PATH,
                    charter_path=CHARTER_PATH,
                    output="json",
                    prompt_type=prompt_type,
                )

            await asyncio.get_event_loop().run_in_executor(None, _run)
            elapsed = time.time() - t0

            async with lock:
                done.add(dataset_id)
                counters["success"] += 1
                idx = counters["success"] + counters["error"]
                print(f"  ✅ [{idx}/{counters['total']}] {slug} ({elapsed:.1f}s)")
                # Save checkpoint after each success
                save_checkpoint(done)

        except Exception as e:
            async with lock:
                counters["error"] += 1
                idx = counters["success"] + counters["error"]
                print(f"  ❌ [{idx}/{counters['total']}] {slug} — {e}")
                counters.setdefault("failed_slugs", []).append(slug)
            logger.error(f"Audit failed for {slug}: {e}")


async def run_audit(rows: list[dict], args, done: set[str]) -> dict:
    """Launch all audits concurrently with a semaphore."""
    semaphore = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    counters = {"success": 0, "error": 0, "total": len(rows)}

    tasks = [audit_one(row, semaphore, args.prompt_type, done, lock, counters) for row in rows]
    await asyncio.gather(*tasks)
    return counters


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    args = parse_args()

    print(f"\n🤖 Bulk LLM Audit — prompt: {args.prompt_type}, concurrency: {args.concurrency}")
    print(f"   DCAT:    {DCAT_PATH}")
    print(f"   Charter: {CHARTER_PATH}\n")

    # Validate reference files
    for path, name in [(DCAT_PATH, "DCAT reference"), (CHARTER_PATH, "Charte")]:
        if not os.path.exists(path):
            print(f"❌ Fichier manquant : {name} → {path}")
            sys.exit(1)

    # Handle checkpoint reset
    if args.reset:
        reset_checkpoint()
    done = load_checkpoint()
    if done:
        print(f"♻️  Checkpoint trouvé : {len(done)} datasets déjà traités, reprise...\n")

    # Fetch candidates
    all_rows = fetch_datasets(args)
    if args.skip_evaluated:
        all_rows = [r for r in all_rows if not r.get("already_evaluated")]

    # Filter out already processed (checkpoint)
    rows = [r for r in all_rows if str(r["id"]) not in done]

    total = len(rows)
    skipped = len(all_rows) - total
    print(f"📊 Total éligibles : {len(all_rows)}")
    if skipped:
        print(f"   ⏭  Ignorés (checkpoint) : {skipped}")
    print(f"   🔄 À traiter : {total}\n")

    if args.dry_run:
        print("[DRY RUN] Datasets qui seraient audités :\n")
        for i, r in enumerate(rows, 1):
            print(f"  {i:4}. {r['slug']} ({r['platform_slug']})")
        return

    if total == 0:
        print("✅ Aucun dataset à auditer.")
        return

    # Run async
    counters = asyncio.run(run_audit(rows, args, done))

    print(f"\n🏁 Terminé : {counters['success']} succès, {counters['error']} erreurs")
    if counters.get("failed_slugs"):
        print("Slugs en erreur :")
        for s in counters["failed_slugs"]:
            print(f"  - {s}")

    # Clean up checkpoint on full success
    if counters["error"] == 0:
        reset_checkpoint()


if __name__ == "__main__":
    main()
