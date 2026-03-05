from typing import Any, Optional

import requests

from settings import OIDC_AUTHORITY, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_REDIRECT_URI


class OIDCClient:
    def __init__(self):
        self._config: Optional[dict[str, Any]] = None

    def _get_config(self) -> dict[str, Any]:
        if self._config is None:
            discovery_url = f"{OIDC_AUTHORITY.rstrip('/')}/.well-known/openid-configuration"
            response = requests.get(discovery_url)
            response.raise_for_status()
            self._config = response.json()
        return self._config

    @property
    def authorization_endpoint(self) -> str:
        return self._get_config()["authorization_endpoint"]

    @property
    def token_endpoint(self) -> str:
        return self._get_config()["token_endpoint"]

    @property
    def userinfo_endpoint(self) -> str:
        return self._get_config()["userinfo_endpoint"]

    def get_authorization_url(self, state: str, nonce: str) -> str:
        params = {
            "client_id": OIDC_CLIENT_ID,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": OIDC_REDIRECT_URI,
            "state": state,
            "nonce": nonce,
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_endpoint}?{query}"

    def exchange_code(self, code: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OIDC_REDIRECT_URI,
            "client_id": OIDC_CLIENT_ID,
            "client_secret": OIDC_CLIENT_SECRET,
        }
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()


oidc_client = OIDCClient()
