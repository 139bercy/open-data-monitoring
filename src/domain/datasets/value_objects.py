from dataclasses import dataclass


@dataclass
class DatasetQuality:
    downloads_count: int
    api_calls_count: int
    has_description: bool
