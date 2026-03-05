from typing import Optional
from uuid import UUID

from domain.auth.aggregate import User
from domain.auth.ports import UserRepository
from infrastructure.database.postgres import PostgresClient


class PostgresUserRepository(UserRepository):
    def __init__(self, client: PostgresClient):
        self.client = client

    def get_by_email(self, email: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE email = %s"
        row = self.client.fetchone(query, (email,))
        if not row:
            return None
        return self._map_to_user(row)

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        query = "SELECT * FROM users WHERE id = %s"
        row = self.client.fetchone(query, (str(user_id),))
        if not row:
            return None
        return self._map_to_user(row)

    def save(self, user: User) -> None:
        query = """
            INSERT INTO users (id, email, hashed_password, full_name, role, created_at, last_login)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                hashed_password = EXCLUDED.hashed_password,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                last_login = EXCLUDED.last_login
        """
        self.client.execute(
            query,
            (
                str(user.id),
                user.email,
                user.hashed_password,
                user.full_name,
                user.role,
                user.created_at,
                user.last_login,
            ),
        )

    def _map_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"],
            last_login=row.get("last_login"),
        )
