from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    role: str = "user"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def __post_init__(self):
        # Basic validation can go here
        pass
