from typing import Optional
from uuid import UUID

from domain.auth.aggregate import User
from domain.auth.ports import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] = None):
        self._users = {u.id: u for u in (users or [])}

    def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)

    def save(self, user: User) -> None:
        self._users[user.id] = user
