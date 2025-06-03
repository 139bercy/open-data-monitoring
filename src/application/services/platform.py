import uuid

from tinydb import Query

from domain.platform.aggregate import Platform
from domain.platform.ports import PlatformRepository


class PlatformMonitoring:
    def __init__(self, adapter_factory, repository: PlatformRepository):
        self.adapter_factory = adapter_factory
        self.PlatformQuery = Query()
        self.repository = repository

    def save(self, aggregate):
        self.repository.save(aggregate)

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

    def get(self, platform_id):
        return self.repository.get(platform_id=platform_id)
