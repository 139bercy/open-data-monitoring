import hashlib
import json
from datetime import datetime
from uuid import UUID

from common import JsonSerializer


class Dataset:
    def __init__(
        self,
        id: UUID,
        platform_id: UUID,
        buid: str,
        slug: str,
        page: str,
        created: datetime,
        modified: datetime,
        published: bool,
        restricted: bool,
        raw: dict,
        publisher: str = None,
    ):
        self.id = id
        self.platform_id = platform_id
        self.buid = buid
        self.slug = slug
        self.page = page
        self.publisher = publisher
        self.created = created
        self.modified = modified
        self.published = published
        self.restricted = restricted
        self.raw = raw
        self.checksum = None
        self.versions = []

    def is_modified_since(self, date: datetime) -> bool:
        return self.modified > date

    def calculate_hash(self) -> str:
        snapshot_str = json.dumps(self.raw, sort_keys=True)
        checksum = hashlib.sha256(snapshot_str.encode()).hexdigest()
        self.checksum = checksum
        return checksum

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=UUID(data["id"]) if not isinstance(data["id"], UUID) else data["id"],
            platform_id=UUID(data["platform_id"]) if not isinstance(data["platform_id"], UUID) else data["platform_id"],
            buid=data["buid"],
            slug=data["slug"],
            page=data["page"],
            created=data["created"] if isinstance(data["created"], datetime) else datetime.fromisoformat(data["created"]),
            modified=data["modified"] if isinstance(data["modified"], datetime) else datetime.fromisoformat(data["modified"]),
            published=bool(data.get("published", True)),
            restricted=bool(data.get("restricted", False)),
            raw=data.get("raw", {}),
            publisher=data.get("publisher"),
        )

    def __repr__(self):
        return f"<Dataset: {self.slug}>"

    def __str__(self):
        return json.dumps(self.__dict__, indent=2, cls=JsonSerializer)
