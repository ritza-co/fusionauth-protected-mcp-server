import os
import logging
import json

import requests
from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider, AccessToken, TokenVerifier
from fastmcp.server.dependencies import get_access_token
from pydantic import AnyHttpUrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FUSIONAUTH_URL = os.environ.get("FUSIONAUTH_URL", "http://fusionauth:9011")
FUSIONAUTH_EXTERNAL_URL = os.environ.get("FUSIONAUTH_EXTERNAL_URL", "http://localhost:9011")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000")
MCP_APP_ID = os.environ.get("MCP_APP_ID", "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e")
MCP_APP_SECRET = os.environ.get("MCP_APP_SECRET", "P6mR6aMjI-c7WJPe1RA95_S6HIpq9xzEqFGhaY5yqDc")
FUSIONAUTH_API_KEY = os.environ.get("FUSIONAUTH_API_KEY", "bf69486b-4733-4470-a592-f1bfce7af580")


class FusionAuthTokenVerifier(TokenVerifier):
    """Verifies tokens by calling FusionAuth's UserInfo endpoint."""

    def __init__(
        self,
        fusionauth_url: str,
        client_id: str,
        client_secret: str | None = None,
        required_scopes: list[str] | None = None,
    ):
        super().__init__(required_scopes=required_scopes)
        self.fusionauth_url = fusionauth_url
        self.client_id = client_id
        self.client_secret = client_secret

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            # Validate token via UserInfo endpoint
            resp = requests.get(
                f"{self.fusionauth_url}/oauth2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )

            if resp.status_code != 200:
                logger.warning("Token validation failed")
                return None

            userinfo = resp.json()

            # Decode token claims
            import base64
            payload_b64 = token.split('.')[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)  # Add padding
            claims = json.loads(base64.urlsafe_b64decode(payload_b64))

            scopes = claims.get("scope", "").split() if claims.get("scope") else []

            return AccessToken(
                token=token,
                client_id=claims.get("sub", ""),
                scopes=scopes,
                expires_at=claims.get("exp"),
                claims=claims,
            )
        except Exception as e:
            logger.error("Failed to validate token: %s", e)
            return None


token_verifier = FusionAuthTokenVerifier(
    fusionauth_url=FUSIONAUTH_URL,
    client_id=MCP_APP_ID,
    client_secret=MCP_APP_SECRET,
    required_scopes=["get_name"],
)

auth = RemoteAuthProvider(
    token_verifier=token_verifier,
    authorization_servers=[AnyHttpUrl(FUSIONAUTH_EXTERNAL_URL)],
    base_url=MCP_SERVER_URL,
)

mcp = FastMCP(
    name="FusionAuth MCP Server",
    auth=auth,
    stateless_http=True,
)


def _lookup_user_name(user_id: str) -> str:
    """Look up a user's name from FusionAuth by user ID."""
    try:
        resp = requests.get(
            f"{FUSIONAUTH_URL}/api/user/{user_id}",
            headers={"Authorization": FUSIONAUTH_API_KEY},
        )
        if resp.status_code == 200:
            user = resp.json().get("user", {})
            first = user.get("firstName", "")
            last = user.get("lastName", "")
            if first or last:
                return f"{first} {last}".strip()
            return user.get("username") or user.get("email") or user_id
    except Exception as e:
        logger.error("Failed to look up user: %s", e)
    return user_id


@mcp.tool()
def get_name() -> str:
    """Get the authenticated user's name from the access token.

    Returns the name of the currently authenticated user. Requires a valid
    FusionAuth access token with the 'get_name' scope.
    """
    access_token = get_access_token()
    if access_token is None:
        return "Error: No access token found. Please authenticate first."

    user_id = access_token.client_id
    name = _lookup_user_name(user_id)

    return f"Hello, {name}!"


if __name__ == "__main__":
    import uvicorn

    mcp_app = mcp.http_app()
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)
