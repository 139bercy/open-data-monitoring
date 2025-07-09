import uuid


class Platform:
    def __init__(
        self,
        id: uuid,
        name: str,
        slug: str,
        type: str,
        url: str,
        organization_id: str,
        key: str,
        datasets_count=0,
        last_sync=None,
        created_at=None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.organization_id = organization_id
        self.type = type
        self.url = url
        self.key = key
        self.datasets_count = datasets_count
        self.last_sync = last_sync
        self.created_at = created_at
        self.syncs = []

    def sync(self, timestamp, status, datasets_count):
        self.datasets_count = datasets_count
        self.last_sync = timestamp
        return {
            "platform_id": self.id,
            "timestamp": timestamp,
            "status": status,
            "datasets_count": datasets_count,
        }

    def add_sync(self, sync):
        self.syncs.append(sync)

    def __str__(self):
        return f"<Platform: {self.name}>"
