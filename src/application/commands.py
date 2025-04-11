from dataclasses import dataclass


@dataclass
class CreatePlatform:
    name: str
    type: str
    url: str
    key: str
