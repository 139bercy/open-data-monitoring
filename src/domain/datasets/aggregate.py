import hashlib
import json
from datetime import datetime
from uuid import UUID

from common import UUIDEncoder


class Dataset:
    def __init__(
        self,
        id: UUID,
        platform_id: UUID,
        buid: str,
        slug: str,
        page: str,
        publisher: str,
        created: datetime,
        modified: datetime,
        raw: dict,
    ):
        self.id = id
        self.platform_id = platform_id
        self.buid = buid
        self.slug = slug
        self.page = page
        self.publisher = publisher
        self.created = created
        self.modified = modified
        self.raw = raw
        self.checksum = None

    def is_modified_since(self, date: datetime) -> bool:
        return self.modified > date

    def calculate_hash(self) -> str:
        snapshot_str = json.dumps(self.raw, sort_keys=True)
        checksum = hashlib.sha256(snapshot_str.encode()).hexdigest()
        self.checksum = checksum
        return checksum

    def __repr__(self):
        return f"<Dataset: {self.slug}>"

    def __str__(self):
        return json.dumps(self.__dict__, indent=2, cls=UUIDEncoder)
