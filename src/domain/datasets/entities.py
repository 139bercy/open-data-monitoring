from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class DatasetVersion:
    """
    Represents a version of a dataset.
    """

    dataset_id: UUID
    snapshot: dict
    checksum: Optional[str] = None
    downloads_count: Optional[int] = None
    api_calls_count: Optional[int] = None
    views_count: Optional[int] = None
    reuses_count: Optional[int] = None
    followers_count: Optional[int] = None
    popularity_score: Optional[float] = None
    diff: Optional[dict] = None
    metadata_volatile: Optional[dict] = None
    timestamp: Optional[datetime] = None

    def __repr__(self):
        return f"<DatasetVersion: {self.dataset_id} :: {self.checksum}>"
