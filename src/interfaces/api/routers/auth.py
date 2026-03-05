import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from domain.auth.aggregate import User
from domain.auth.exceptions import UnauthorizedError
from domain.auth.user_service import OIDCUserService
from infrastructure.security import create_access_token, verify_password
from infrastructure.security.oidc import oidc_client
from interfaces.api.dependencies import get_current_user
from interfaces.api.schemas.auth import Token, UserOut
from settings import app as domain_app

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Classic username/password login for local users.
    """
    user = domain_app.uow.users.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/login/proconnect")
async def login_proconnect():
    """
    Redirect the user to ProConnect authorization endpoint.
    """
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    # Note: In a real app, state and nonce should be stored in a secure cookie or session
    auth_url = oidc_client.get_authorization_url(state=state, nonce=nonce)
    return RedirectResponse(auth_url)


@router.get("/callback")
async def auth_callback(code: str, state: str):
    """
    OIDC callback endpoint. Exchanges code for token and logs in the user.
    """
    try:
        # 1. Exchange code for tokens
        tokens = oidc_client.exchange_code(code)

        # 2. Get user info from ID Token or UserInfo endpoint
        user_info = oidc_client.get_user_info(tokens["access_token"])

        # 3. Map to local user (JIT Provisioning)
        user_service = OIDCUserService(domain_app.uow.users)
        user = user_service.get_or_create_user(user_info)

        # 4. Create local JWT session
        access_token = create_access_token(data={"sub": user.email})

        # 5. Redirect to frontend with token (or set cookie)
        # For now, redirect to a frontend success page or home with token in fragment
        return RedirectResponse(f"/#access_token={access_token}")

    except Exception as e:
        logger.error(f"OIDC callback error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {str(e)}")


@router.get("/me", response_model=UserOut)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Retrieve current authenticated user information.
    """
    return current_user
