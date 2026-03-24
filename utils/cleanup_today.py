import argparse
import os
import sys
from datetime import date, datetime

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from logger import logger
from settings import app


def cleanup_today(target_date: date = None):
    if target_date is None:
        target_date = date.today()

    target_str = target_date.strftime("%Y-%m-%d")
    logger.info(f"🧹 Starting cleanup for datasets added on {target_str}")

    with app.uow:
        # 1. Identify datasets added on target_date
        query_find = (
            "SELECT id, slug FROM datasets WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)"
        )
        datasets = app.uow.datasets.client.fetchall(query_find, (target_str, target_str))

        if not datasets:
            logger.info("✨ No datasets found for this day.")
            return

        dataset_ids = [str(d["id"]) for d in datasets]
        logger.info(f"📋 Found {len(dataset_ids)} datasets to remove.")

        # Security prompt
        print(
            f"\n⚠️  ATTENTION: Vous allez supprimer définitivement {len(dataset_ids)} jeux de données du {target_str}."
        )
        confirm = input(f"👉 Pour confirmer, veuillez saisir la date cible ({target_str}) : ")

        if confirm != target_str:
            logger.warning("❌ Confirmation incorrecte. Nettoyage annulé.")
            return

        # 2. Delete in correct order to respect FKs
        # Note: dataset_blobs should cascade from datasets if defined with ON DELETE CASCADE
        # but dataset_versions might block it if it's not cascading.

        try:
            # Delete versions first
            logger.info("🗑️ Removing dataset versions...")
            app.uow.datasets.client.execute(
                "DELETE FROM dataset_versions WHERE dataset_id = ANY(%s::uuid[])", (dataset_ids,)
            )

            # Delete quality records
            logger.info("🗑️ Removing dataset quality records...")
            app.uow.datasets.client.execute(
                "DELETE FROM dataset_quality WHERE dataset_id = ANY(%s::uuid[])", (dataset_ids,)
            )

            # Delete datasets (this will cascade to blobs)
            logger.info("🗑️ Removing dataset records (cascading to blobs)...")
            app.uow.datasets.client.execute("DELETE FROM datasets WHERE id = ANY(%s::uuid[])", (dataset_ids,))

            logger.info(f"✅ Cleanup completed successfully for {len(dataset_ids)} datasets.")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup datasets added on a specific day.")
    parser.add_argument("--date", type=str, help="Date to cleanup (YYYY-MM-DD), defaults to today.")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    cleanup_today(target_date)
