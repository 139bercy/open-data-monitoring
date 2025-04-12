from dataclasses import dataclass
from datetime import datetime

from eventsourcing.domain import Aggregate, event


@dataclass
class Sync(Aggregate):
    timestamp: datetime
    status: str
    datasets_count: int


class Platform(Aggregate):
    @event("Created")
    def __init__(self, name, type, url, key):
        self.name = name
        self.type = type
        self.url = url
        self.key = key
        self.datasets_count: int = 0
        self.last_sync: datetime = None

    @event("Synced")
    def sync(self, timestamp, status, datasets_count):
        self.datasets_count = datasets_count
        self.last_sync = datetime.now()

    def __str__(self):
        return {
            "name": self.name,
            "url": self.url,
            "type": self.type,
            "key": self.key,
        }