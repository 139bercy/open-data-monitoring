from uuid import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from common import get_base_url
from domain.datasets.aggregate import Dataset
from domain.platform.aggregate import Platform
from exceptions import DatasetHasNotChanged, DatasetUnreachableError
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


def find_platform_from_url(app: App, url: str) -> Platform | None:
    with app.uow:
        try:
            return app.platform.repository.get_by_domain(get_base_url(url))
        except ValueError:
            return None


def find_dataset_id_from_url(app: App, url: str) -> str | None:
    platform = find_platform_from_url(app=app, url=url)
    if platform is None:
        return None
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset_id = adapter.find_dataset_id(url=url)
    return dataset_id


def upsert_dataset(app: App, platform: Platform, dataset: dict) -> UUID:
    with app.uow:
        if dataset.get("sync_status", None) == "failed":
            dataset_id = app.dataset.repository.get_id_by_slug(platform_id=platform.id, slug=dataset["slug"])
            app.dataset.repository.update_dataset_sync_status(
                platform_id=platform.id, dataset_id=dataset_id, status="failed"
            )
    instance = app.dataset.add_dataset(platform=platform, dataset=dataset)
    if instance is None:
        return
    with app.uow:
        instance.calculate_hash()
        existing_checksum = app.dataset.repository.get_checksum_by_buid(instance.buid)
        if existing_checksum == instance.checksum:
            logger.debug(
                f"{platform.type.upper()} - Dataset '{instance.slug}' already exists with identical checksum, "
                f"skipping."
            )
            return instance.id
        existing_dataset = app.dataset.repository.get_by_buid(instance.buid)
        if existing_dataset:
            instance.id = existing_dataset.id
            app.dataset.repository.add(dataset=instance)
            add_version(app=app, dataset_id=str(existing_dataset.id), instance=instance)
            dataset_id = existing_dataset.id
            logger.info(f"{platform.type.upper()} - Dataset '{instance.slug}' has changed. New version created")
        else:
            logger.warning(f"{platform.type.upper()} - New dataset '{instance.slug}'.")
            app.dataset.repository.add(dataset=instance)
            add_version(app=app, dataset_id=str(instance.id), instance=instance)
            dataset_id = instance.id
        app.dataset.repository.update_dataset_sync_status(
            platform_id=platform.id, dataset_id=instance.id, status="success"
        )
        return dataset_id


def add_version(app: App, dataset_id: str, instance: Dataset) -> None:
    app.dataset.repository.add_version(
        dataset_id=UUID(dataset_id),
        snapshot=instance.raw,
        checksum=instance.checksum,
        downloads_count=instance.downloads_count,
        api_calls_count=instance.api_calls_count,
    )


def fetch_dataset(platform: Platform, dataset_id: str) -> dict | None:
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
