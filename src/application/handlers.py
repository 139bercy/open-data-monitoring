from uuid import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from application.services.platform import PlatformMonitoring
from common import get_base_url
from domain.datasets.aggregate import Dataset
from infrastructure.factories.dataset import DatasetAdapterFactory


def create_platform(app, data: dict) -> UUID:
    cmd = CreatePlatform(**data)
    platform = app.register(
        name=cmd.name,
        slug=cmd.slug,
        organization_id=cmd.organization_id,
        type=cmd.type,
        url=cmd.url,
        key=cmd.key,
    )
    app.save(platform)
    return platform.id


def sync_platform(app: PlatformMonitoring, platform_id: UUID) -> None:
    cmd = SyncPlatform(id=platform_id)
    app.sync_platform(platform_id=cmd.id)
    return


def find_platform_from_url(app, url):
    base_url = get_base_url(url=url)
    platform = app.platform.repository.get_by_domain(base_url)
    return platform


def find_dataset_id_from_url(app, url):
    platform = find_platform_from_url(app=app, url=url)
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset_id = adapter.find_dataset_id(url=url)
    return dataset_id


def add_dataset(app, platform_type: str, dataset: Dataset):
    dataset = app.dataset.add_dataset(platform_type=platform_type, dataset=dataset)
    dataset.calculate_hash()
    app.dataset.repository.add(dataset=dataset)
    return dataset.id


def fetch_dataset(platform, dataset_id):
    factory = DatasetAdapterFactory()
    adapter = factory.create(platform_type=platform.type)
    dataset = adapter.fetch(platform.url, platform.key, dataset_id)
    return dataset
