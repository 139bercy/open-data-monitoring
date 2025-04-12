from eventsourcing.application import Application

from domain.platform.aggregate import Platform


class DataMonitoring(Application):
    def __init__(self, adapter_factory):
        super().__init__()
        self.adapter_factory = adapter_factory

    def register_platform(self, name: str, type: str, url: str, key: str):
        platform = Platform(name, type, url, key)
        self.save(platform)
        return platform.id

    def get_platform(self, platform_id):
        platform = self.repository.get(platform_id)
        assert isinstance(platform, Platform)
        return platform

    def sync_platform(self, platform_id):
        platform = self.get_platform(platform_id=platform_id)
        adapter = self.adapter_factory.create(
            platform.type,
            platform.url,
            platform.key, platform.name
        )
        datasets_count = adapter.fetch_datasets()
        platform.sync(datasets_count)
        self.save(platform)