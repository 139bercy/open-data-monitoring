import logging
from typing import Any

from domain.auth.aggregate import User
from domain.auth.ports import UserRepository

logger = logging.getLogger(__name__)


class OIDCUserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_or_create_user(self, user_info: dict[str, Any]) -> User:
        """
        Map OIDC UserInfo to local User aggregate.
        Handles Just-in-Time provisioning.
        """
        email = user_info.get("email")
        if not email:
            raise ValueError("OIDC UserInfo missing email")

        user = self.repository.get_by_email(email)

        if not user:
            logger.info(f"Creating new JIT user for {email}")
            user = User(
                email=email,
                full_name=user_info.get("name")
                or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip(),
                hashed_password="OIDC_USER",  # Dummy value, OIDC users don't use local password
                role="user",
            )
            self.repository.save(user)
        else:
            # Update full name if it changed or was missing
            new_name = user_info.get("name")
            if new_name and user.full_name != new_name:
                user.full_name = new_name
                self.repository.save(user)

        return user
