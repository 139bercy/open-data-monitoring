from dataclasses import dataclass


@dataclass
class DatasetDTO:
    buid: str
    slug: str
    page: str
    publisher: str
    created: str
    modified: str
