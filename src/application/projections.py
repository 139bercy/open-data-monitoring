from tinydb import TinyDB, Query

from domain.aggregate import Platform

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

# Configuration de la sérialisation
serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), 'TinyDate')


class TinyDbPlatformRepository:
    def __init__(self, name):
        self.name = name
        self.db = TinyDB(name, indent=2, ensure_ascii=False, storage=serialization)
        self.metadata = self.db.table("metadata")
        self.query = Query()

    def project(self, event, aggregate_id):
        if isinstance(event, Platform.Created):
            self._create_platform(event=event, aggregate_id=aggregate_id)

        elif isinstance(event, Platform.Synced):
            self._sync_platform(event=event, aggregate_id=aggregate_id)

    def _create_platform(self, event, aggregate_id):
        if not self.db.contains(self.query.id == aggregate_id):
            print(event)
            self.db.insert(
                {
                    "id": aggregate_id,
                    "name": event.name,
                    "type": event.type,
                    "url": event.url,
                    "key": event.key,
                    "datasets_count": 0,
                    "sync": []
                }
            )

    def _sync_platform(self, event, aggregate_id):
        data = self.db.search(self.query.id == aggregate_id)
        if not data:
            raise ValueError(f"Aucune plateforme trouvée pour l'ID {aggregate_id}")

        existing_data = data[0]
        sync_history = existing_data.get("sync", []) or []  # Garantit une liste
        datasets_changes = event.datasets_count - existing_data["datasets_count"]
        payload = {
            "timestamp": event.timestamp,
            "status": event.status,
            "datasets_count": event.datasets_count,
            "datasets_changes": datasets_changes
        }
        new_sync_history = sync_history + [payload]
        self.db.update({
            "last_sync": event.timestamp,
            "datasets_count": event.datasets_count,
            "sync": new_sync_history
        }, self.query.id == str(aggregate_id))