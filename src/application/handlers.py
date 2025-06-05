from uuid import UUID

from application.commands.platform import CreatePlatform, SyncPlatform
from application.services.platform import PlatformMonitoring
from domain.datasets.aggregate import Dataset


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


def add_dataset(app, platform_type: str, dataset: Dataset):
    dataset = app.add_dataset(platform_type=platform_type, dataset=dataset)
    dataset.calculate_hash()
    app.repository.add(dataset=dataset)
    return dataset.id
