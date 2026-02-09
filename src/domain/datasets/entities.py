from dataclasses import dataclass
from typing import Optional


@dataclass
class DatasetVersion:
    """
    Represents a version of a dataset.
    """
    dataset_id: str
    snapshot: dict
    checksum: str
    downloads_count: Optional[int] = None
    api_calls_count: Optional[int] = None
    views_count: Optional[int] = None
    reuses_count: Optional[int] = None
    followers_count: Optional[int] = None
    popularity_score: Optional[float] = None
    diff: Optional[dict] = None
    metadata_volatile: Optional[dict] = None

    def __repr__(self):
        return f"<DatasetVersion: {self.dataset_id} :: {self.checksum}>"
