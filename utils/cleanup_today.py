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
        # 1. Platform Sync Histories (No dependencies)
        logger.info(f"🗑️ Removing platform sync histories from {target_str}...")
        app.uow.datasets.client.execute(
            "DELETE FROM platform_sync_histories WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)",
            (target_str, target_str),
        )

        # 2. Identify full datasets added on target_date
        query_find = (
            "SELECT id, slug FROM datasets WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)"
        )
        new_datasets = app.uow.datasets.client.fetchall(query_find, (target_str, target_str))
        new_dataset_ids = [str(d["id"]) for d in new_datasets]

        # 3. Security prompt (Show context)
        # We also count total versions/blobs to remove
        count_v = app.uow.datasets.client.fetchone(
            "SELECT count(*) FROM dataset_versions WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)",
            (target_str, target_str),
        )["count"]
        count_b = app.uow.datasets.client.fetchone(
            "SELECT count(*) FROM dataset_blobs WHERE created_at >= %s AND created_at < (%s::date + '1 day'::interval)",
            (target_str, target_str),
        )["count"]

        print("\n⚠️  ATTENTION: Vous allez supprimer définitivement :")
        print(f"   - {len(new_dataset_ids)} nouveaux jeux de données")
        print(f"   - {count_v} nouvelles versions")
        print(f"   - {count_b} nouveaux blobs")
        print("   - Tous les historiques de sync de la journée")

        confirm = input(f"👉 Pour confirmer le nettoyage du {target_str}, veuillez saisir la date cible : ")

        if confirm != target_str:
            logger.warning("❌ Confirmation incorrecte. Nettoyage annulé.")
            return

        # 4. Starting deletions
        try:
            # Delete versions first (to free up blobs and datasets)
            logger.info("🗑️ Removing dataset versions...")
            app.uow.datasets.client.execute(
                "DELETE FROM dataset_versions WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)",
                (target_str, target_str),
            )

            # Delete quality records added today
            logger.info("🗑️ Removing dataset quality reports...")
            app.uow.datasets.client.execute(
                "DELETE FROM dataset_quality WHERE timestamp >= %s AND timestamp < (%s::date + '1 day'::interval)",
                (target_str, target_str),
            )

            # Delete blobs added today
            logger.info("🗑️ Removing dataset blobs...")
            app.uow.datasets.client.execute(
                "DELETE FROM dataset_blobs WHERE created_at >= %s AND created_at < (%s::date + '1 day'::interval)",
                (target_str, target_str),
            )

            # Delete full datasets added today
            if new_dataset_ids:
                logger.info(f"🗑️ Removing {len(new_dataset_ids)} dataset records...")
                app.uow.datasets.client.execute("DELETE FROM datasets WHERE id = ANY(%s::uuid[])", (new_dataset_ids,))

            logger.info(f"✅ Cleanup completed successfully for {target_str}.")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup datasets added on a specific day.")
    parser.add_argument("--date", type=str, help="Date to cleanup (YYYY-MM-DD), defaults to today.")
    args = parser.parse_args()

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
    cleanup_today(target_date)
