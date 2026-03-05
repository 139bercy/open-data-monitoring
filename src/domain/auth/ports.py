from typing import Optional, Protocol
from uuid import UUID

from domain.auth.aggregate import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> Optional[User]: ...

    def get_by_id(self, user_id: UUID) -> Optional[User]: ...

    def save(self, user: User) -> None: ...
