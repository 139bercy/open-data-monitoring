import json
from datetime import datetime
from uuid import UUID

from common import UUIDEncoder


class Dataset:
    def __init__(
        self,
        id: UUID,
        buid: str,
        slug: str,
        page: str,
        publisher: str,
        created: datetime,
        modified: datetime,
    ):
        self.id = id
        self.buid = buid
        self.slug = slug
        self.page = page
        self.publisher = publisher
        self.created = created
        self.modified = modified

    def __repr__(self):
        return f"<Dataset: {self.slug}>"

    def __str__(self):
        return json.dumps(self.__dict__, indent=2, cls=UUIDEncoder)
