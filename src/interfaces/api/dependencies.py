from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from domain.auth.aggregate import User
from domain.auth.exceptions import UnauthorizedError, UserNotFoundError
from settings import ALGORITHM, SECRET_KEY
from settings import app as domain_app

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency to retrieve the current authenticated user from a JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise UnauthorizedError("Invalid token: missing subject")
    except JWTError:
        raise UnauthorizedError("Invalid token: failed to decode")

    with domain_app.uow as uow:
        user = uow.users.get_by_email(email)
        if user is None:
            raise UserNotFoundError(f"User not found for email: {email}")
        return user
