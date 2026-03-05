from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from domain.unit_of_work import UnitOfWork
from infrastructure.security import create_access_token, verify_password
from settings import ACCESS_TOKEN_EXPIRE_MINUTES


@dataclass
class LoginCommand:
    email: str
    password: str


@dataclass
class LoginOutput:
    status: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    message: Optional[str] = None


class LoginUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def handle(self, command: LoginCommand) -> LoginOutput:
        with self.uow:
            user = self.uow.users.get_by_email(command.email)
            if not user:
                return LoginOutput(status="failed", message="Invalid email or password")

            if not verify_password(command.password, user.hashed_password):
                return LoginOutput(status="failed", message="Invalid email or password")

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

            return LoginOutput(status="success", access_token=access_token, token_type="bearer")
