from dataclasses import dataclass


@dataclass
class DatasetQuality:
    downloads_count: int | None
    api_calls_count: int | None
    has_description: bool
    is_slug_valid: bool
    evaluation_results: dict | None = None
