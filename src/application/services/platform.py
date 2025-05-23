from eventsourcing.application import Application
from eventsourcing.system import NotificationLogReader
from tinydb import Query

from domain.platform.aggregate import Platform


class PlatformMonitoring(Application):
    def __init__(self, adapter_factory, repository):
        super().__init__()
        self.reads = repository
        self.adapter_factory = adapter_factory
        self.reader = NotificationLogReader(self.notification_log)
        self.PlatformQuery = Query()
        self.last_processed_id = self.get_last_processed_id()

    def save(self, aggregate):
        super().save(aggregate)
        self.process_new_events()

    def get_platform(self, platform_id):
        platform = self.repository.get(platform_id)
        assert isinstance(platform, Platform)
        return platform

    def get_all_platforms(self):
        return self.reads.db.all()

    def register_platform(
        self,
        name: str,
        slug: str,
        organization_id: str,
        type: str,
        url: str,
        key: str = None,
    ):
        platform = Platform(
            name=name,
            slug=slug,
            organization_id=organization_id,
            type=type,
            url=url,
            key=key,
        )
        self.save(platform)
        return platform.id

    def sync_platform(self, platform_id):
        platform = self.get_platform(platform_id=platform_id)
        adapter = self.adapter_factory.create(
            platform_type=platform.type,
            url=platform.url,
            key=platform.key,
            slug=platform.slug,
        )
        payload = adapter.fetch()
        platform.sync(**payload)
        self.save(platform)

    def process_new_events(self):
        """Traite les nouveaux événements depuis la dernière notification"""
        notifications = self.reader.read(start=self.last_processed_id + 1)
        for notification in notifications:
            self.apply_projection(notification)
            self.save_last_processed_id(notification.id)

    def apply_projection(self, notification):
        event = self.mapper.to_domain_event(notification)
        aggregate_id = str(event.originator_id)
        self.reads.project(event=event, aggregate_id=aggregate_id)

    def save_last_processed_id(self, last_id):
        self.reads.metadata.upsert(
            {"type": "metadata", "last_processed_id": last_id},
            Query()["type"] == "metadata",  # Syntaxe corrigée ici
        )

    def get_last_processed_id(self):
        doc = self.reads.metadata.get(Query()["type"] == "metadata")
        return doc.get("last_processed_id", 0) if doc else 0
