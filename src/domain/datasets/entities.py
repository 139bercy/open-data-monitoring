from dataclasses import dataclass


@dataclass
class DatasetVersion:
    dataset_id: str
    snapshot: dict
    checksum: str
