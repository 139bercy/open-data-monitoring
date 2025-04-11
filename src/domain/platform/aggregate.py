from datetime import datetime

from eventsourcing.domain import Aggregate, event


class Platform(Aggregate):
    @event("Created")
    def __init__(self, name, type, url, key):
        self.name = name
        self.type = type
        self.url = url
        self.key = key
        self.datasets_count = None
        self.last_sync: datetime = None
