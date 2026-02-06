from dataclasses import dataclass
from typing import Optional


@dataclass
class DatasetQuality:
    downloads_count: Optional[int]
    api_calls_count: Optional[int]
    has_description: bool
    is_slug_valid: bool
