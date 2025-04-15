from dataclasses import dataclass
from datetime import datetime

from eventsourcing.domain import Aggregate, event


class Platform(Aggregate):
    @event("Created")
    def __init__(
        self, name: str, slug: str, type: str, url: str, organization_id: str, key: str
    ):
        self.name = name
        self.slug = slug
        self.organization_id = organization_id
        self.type = type
        self.url = url
        self.key = key
        self.datasets_count: int = 0
        self.last_sync: datetime = None

    @event("Synced")
    def sync(self, timestamp, status, datasets_count):
        self.datasets_count = datasets_count
        self.last_sync = datetime.now()
