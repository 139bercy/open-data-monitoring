from datetime import datetime

from eventsourcing.domain import Aggregate, event


class Dataset(Aggregate):
    @event("Created")
    def __init__(
            self,
            buid: str,
            slug: str,
            page: str,
            publisher: str,
            created: datetime,
            modified: datetime,
    ):
        self.buid = buid
        self.slug = slug
        self.page = page
        self.publisher = publisher
        self.created = created
        self.modified = modified

