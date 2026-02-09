from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from common import get_base_url
from domain.datasets.aggregate import Dataset
from domain.platform.aggregate import Platform
from exceptions import DatasetUnreachableError
from infrastructure.factories.dataset import DatasetAdapterFactory
from logger import logger
from settings import App


def create_platform(app: App, data: dict) -> UUID:
    cmd = CreatePlatform(**data)
    with app.uow:
        platform = app.platform.register(
            name=cmd.name,
            slug=cmd.slug,
            organization_id=cmd.organization_id,
            type=cmd.type,
            url=cmd.url,
            key=cmd.key,
        )
        app.platform.save(platform)
        return platform.id


def sync_platform(app: App, platform_id: UUID) -> None:
    cmd = SyncPlatform(id=platform_id)
    with app.uow:
        app.platform.sync_platform(platform_id=cmd.id)


def find_platform_from_url(app: App, url: str) -> Optional[Platform]:
    print(url)
    with app.uow:
        try:
            return app.platform.repository.get_by_domain(get_base_url(url))
        except ValueError:
            return None


def find_dataset_id_from_url(app: App, url: str) -> Optional[str]:
    platform = find_platform_from_url(app=app, url=url)
    if platform is None:
        return None
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset_id = adapter.find_dataset_id(url=url)
    return dataset_id


def _handle_failed_sync_status(app: App, platform: Platform, dataset: dict) -> None:
    """Handle failed sync status update before processing."""
    if dataset.get("sync_status") == "failed":
        dataset_id = app.dataset.repository.get_id_by_slug(platform_id=platform.id, slug=dataset["slug"])
        app.dataset.repository.update_dataset_sync_status(
            platform_id=platform.id, dataset_id=dataset_id, status="failed"
        )


def _has_metrics_changed(existing: Dataset, new: Dataset) -> bool:
    """Check if harmonized metrics have changed between versions."""
    return (
        existing.downloads_count != new.downloads_count
        or existing.api_calls_count != new.api_calls_count
        or existing.views_count != new.views_count
        or existing.reuses_count != new.reuses_count
        or existing.followers_count != new.followers_count
        or existing.popularity_score != new.popularity_score
    )


def _is_cooldown_active(existing: Optional[Dataset]) -> bool:
    """Check if 24h cooldown period is active for metric-only changes."""
    if not existing or not existing.last_version_timestamp:
        return False

    now = datetime.now(timezone.utc)
    last_ts = existing.last_version_timestamp
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)

    return (now - last_ts) < timedelta(hours=24)


def _should_create_version(
    existing: Optional[Dataset], instance: Dataset, metrics_changed: bool, is_cooldown: bool
) -> bool:
    """Determine if a new version should be created."""
    if not existing:
        return True
    if existing.checksum != instance.checksum:
        return True
    if existing.is_deleted != instance.is_deleted:
        return True
    if metrics_changed and not is_cooldown:
        return True
    return False


def _create_or_update_dataset_version(
    app: App, platform: Platform, instance: Dataset, existing: Optional[Dataset]
) -> UUID:
    """Persist dataset and create new version."""
    if existing:
        instance.id = existing.id
        app.dataset.repository.add(dataset=instance)
        add_version(app=app, dataset_id=str(existing.id), instance=instance)
        logger.info(f"{platform.type.upper()} - Dataset '{instance.slug}' has changed. New version created")
        return existing.id
    else:
        logger.warning(f"{platform.type.upper()} - New dataset '{instance.slug}'.")
        app.dataset.repository.add(dataset=instance)
        add_version(app=app, dataset_id=str(instance.id), instance=instance)
        return instance.id


def upsert_dataset(app: App, platform: Platform, dataset: dict) -> UUID:
    """Upsert a dataset and create a new version if needed."""
    # 1. Handle failed sync status
    with app.uow:
        _handle_failed_sync_status(app, platform, dataset)

    # 2. Create domain instance
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    instance = app.dataset.add_dataset(platform=platform, dataset=dataset, adapter=adapter)
    if instance is None:
        return

    instance.is_deleted = False

    with app.uow:
        instance.calculate_hash()
        existing = app.dataset.repository.get_by_buid(instance.buid)

        # 3. Determine versioning decision
        metrics_changed = _has_metrics_changed(existing, instance) if existing else False
        is_cooldown = _is_cooldown_active(existing)
        should_version = _should_create_version(existing, instance, metrics_changed, is_cooldown)

        logger.debug(
            f"Version check for {instance.slug}: metrics_changed={metrics_changed}, "
            f"is_cooldown={is_cooldown}, should_version={should_version}"
        )

        if not should_version:
            logger.debug(f"{platform.type.upper()} - Dataset '{instance.slug}' has not changed (Cooldown or No change).")
            return instance.id

        # 4. Create version
        dataset_id = _create_or_update_dataset_version(app, platform, instance, existing)

        # 5. Update sync status
        app.dataset.repository.update_dataset_sync_status(
            platform_id=platform.id, dataset_id=dataset_id, status="success"
        )
        return dataset_id


def add_version(app: App, dataset_id: str, instance: Dataset) -> None:
    app.dataset.repository.add_version(
        dataset_id=UUID(dataset_id),
        snapshot=instance.raw,
        checksum=instance.checksum,
        title=instance.title,
        downloads_count=instance.downloads_count,
        api_calls_count=instance.api_calls_count,
        views_count=instance.views_count,
        reuses_count=instance.reuses_count,
        followers_count=instance.followers_count,
        popularity_score=instance.popularity_score,
    )


def fetch_dataset(platform: Platform, dataset_id: str) -> Optional[dict]:
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    try:
        dataset = adapter.fetch(platform.url, platform.key, dataset_id)
        return dataset
    except DatasetUnreachableError:
        logger.error(f"{platform.type.upper()} - Fetch Dataset - Dataset '{dataset_id}' not found")
        return {"platform_id": platform.id, "slug": dataset_id, "sync_status": "failed"}


def get_publishers_stats(app: App) -> list[dict[str, any]]:
    """
    Récupère les statistiques des publishers via la méthode repository propre.
    Version DDD-compliant pour remplacer l'accès direct au client dans la CLI.
    """
    with app.uow:
        return app.dataset.repository.get_publishers_stats()


def check_deleted_datasets(app, platform, datasets):
    with app.uow:
        in_base = app.dataset.repository.get_buids(platform_id=platform.id)
        # On supporte 'uid' (ODS) et 'id' (data.gouv)
        in_crawler = [d.get("uid") or d.get("id") or d.get("dataset_id") for d in datasets]
        deleted = set(in_base) - set(in_crawler)
        for buid in deleted:
            dataset = app.dataset.repository.get_by_buid(dataset_buid=buid)
            if dataset:
                dataset.is_deleted = True
                app.dataset.repository.update_dataset_state(dataset)
                logger.info(f"{platform.type.upper()} - Dataset '{dataset.slug}' deleted")

