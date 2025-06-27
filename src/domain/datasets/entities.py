from dataclasses import dataclass


@dataclass
class DatasetVersion:
    dataset_id: str
    snapshot: dict
    checksum: str
    downloads_count: int
    api_calls_count: int
