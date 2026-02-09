from dataclasses import dataclass


@dataclass
class DatasetVersion:
    """
    Represents a version of a dataset.
    """

    dataset_id: str
    snapshot: dict
    checksum: str
    downloads_count: int | None = None
    api_calls_count: int | None = None
    views_count: int | None = None
    reuses_count: int | None = None
    followers_count: int | None = None
    popularity_score: float | None = None
    diff: dict | None = None
    metadata_volatile: dict | None = None

    def __repr__(self):
        return f"<DatasetVersion: {self.dataset_id} :: {self.checksum}>"
