from eventsourcing.application import Application

from domain.platform.aggregate import Platform


class DataMonitoring(Application):

    def register_platform(self, name: str, type: str, url: str, key: str):
        platform = Platform(name, type, url, key)
        self.save(platform)
        return platform.id

    def get_platform(self, platform_id):
        platform = self.repository.get(platform_id)
        assert isinstance(platform, Platform)
        return platform

