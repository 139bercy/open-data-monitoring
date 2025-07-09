import uuid

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository
from infrastructure.factories.platform import PlatformAdapterFactory


class PlatformMonitoring:
    def __init__(self, repository: PlatformRepository):
        self.factory = PlatformAdapterFactory()
        self.repository = repository

    def save(self, aggregate):
        self.repository.save(aggregate)

    def get(self, platform_id):
        return self.repository.get(platform_id=platform_id)

    def get_all_platforms(self):
        return self.repository.all()

    def register(
        self,
        name: str,
        slug: str,
        organization_id: str,
        type: str,
        url: str,
        key: str = None,
    ):
        platform = Platform(
            id=uuid.uuid4(),
            name=name,
            slug=slug,
            organization_id=organization_id,
            type=type,
            url=url,
            key=key,
        )
        return platform

    def sync_platform(self, platform_id):
        platform = self.repository.get(platform_id=platform_id)
        adapter = self.factory.create(
            platform_type=platform.type,
            url=platform.url,
            key=platform.key,
            slug=platform.slug,
        )
        payload = adapter.fetch()
        platform.sync(**payload)
        self.repository.save_sync(platform_id=platform_id, payload=payload)
