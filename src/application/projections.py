from tinydb import TinyDB, Query

from domain.aggregate import Platform


class TinyDbPlatformRepository:
    def __init__(self, name):
        self.name = name
        self.db = TinyDB(name, indent=2, ensure_ascii=False)
        self.metadata = self.db.table("metadata")
        self.query = Query()

    def project(self, event, aggregate_id):
        if isinstance(event, Platform.Created):
            self._create_platform(event=event, aggregate_id=aggregate_id)

        elif isinstance(event, Platform.Synced):
            self._sync_platform(event=event, aggregate_id=aggregate_id)

    def _create_platform(self, event, aggregate_id):
        if not self.db.contains(self.query.id == aggregate_id):
            self.db.insert(
                {
                    "id": aggregate_id,
                    "name": event.name,
                    "type": event.type,
                    "url": event.url,
                    "datasets_count": 0,
                }
            )

    def _sync_platform(self, event, aggregate_id):
        self.db.update(
            {"datasets_count": event.datasets_count}, self.query.id == aggregate_id
        )
