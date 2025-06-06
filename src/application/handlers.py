from uuid import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from common import get_base_url
from domain.platform.aggregate import Platform
from infrastructure.factories.dataset import DatasetAdapterFactory
from settings import App


def create_platform(app: App, data: dict) -> UUID:
    cmd = CreatePlatform(**data)
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
    app.platform.sync_platform(platform_id=cmd.id)
    return


def find_platform_from_url(app: App, url: str) -> Platform:
    base_url = get_base_url(url=url)
    platform = app.platform.repository.get_by_domain(base_url)
    return platform


def find_dataset_id_from_url(app: App, url: str) -> UUID:
    platform = find_platform_from_url(app=app, url=url)
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset_id = adapter.find_dataset_id(url=url)
    return dataset_id


def add_dataset(app: App, platform: Platform, dataset: dict) -> UUID:
    instance = app.dataset.add_dataset(platform=platform, dataset=dataset)
    instance.calculate_hash()
    app.dataset.repository.add(dataset=instance)
    return instance.id


def fetch_dataset(platform: Platform, dataset_id: UUID) -> dict:
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset = adapter.fetch(platform.url, platform.key, dataset_id)
    return dataset
