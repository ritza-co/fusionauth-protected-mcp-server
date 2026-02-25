#!/usr/bin/env python3
"""
MCP Client Setup Script

Registers an MCP client as an OAuth application in FusionAuth so it can
authenticate against the MCP server. Run this script once for each MCP
client you want to register.

Usage:
    python setup_clients.py [--fusionauth-url URL] [--api-key KEY]
"""

import argparse
import json
import sys
import uuid

import requests

FUSIONAUTH_URL = "http://localhost:9011"
API_KEY = "bf69486b-4733-4470-a592-f1bfce7af580"
MCP_SERVER_APP_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"

REDIRECT_URLS = [
    "http://localhost:*/oauth/callback",
    "http://127.0.0.1:*/oauth/callback",
]

CONNECTOR_UI_REDIRECT_URL = "https://claude.ai/api/mcp/auth_callback"


def check_fusionauth(base_url: str, api_key: str) -> bool:
    """Check if FusionAuth is running and the API key is valid."""
    try:
        resp = requests.get(
            f"{base_url}/api/status",
            headers={"Authorization": api_key},
        )
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def create_scope(base_url: str, api_key: str, app_id: str) -> bool:
    """Try to create the get_name custom scope on the MCP Server application."""
    resp = requests.post(
        f"{base_url}/api/application/{app_id}/scope",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json={
            "scope": {
                "name": "get_name",
                "description": "Access the get_name tool to retrieve the authenticated user's name",
                "defaultConsentMessage": "Allow this application to read your name",
                "defaultConsentDetail": "This will share your display name with the requesting application.",
                "required": True,
            }
        },
    )

    if resp.status_code in (200, 201):
        return True
    elif resp.status_code == 400:
        error_data = resp.json()
        field_errors = error_data.get("fieldErrors", {})
        general_errors = error_data.get("generalErrors", [])
        if "scope.name" in field_errors:
            # Scope already exists, treat as success
            return True
        for err in general_errors:
            if "license" in err.get("message", "").lower():
                print("  Note: Custom scopes require a FusionAuth Essentials license.")
                print("  The MCP server will still work, but without the custom 'get_name' scope.")
                return False
        print(f"  Failed to create scope: {resp.status_code}")
        return False
    else:
        print(f"  Failed to create scope: {resp.status_code}")
        return False


def create_client_application(
    base_url: str, api_key: str, client_name: str, connector_ui: bool = False
) -> "dict | None":
    """Create an OAuth application in FusionAuth for an MCP client."""
    app_id = str(uuid.uuid4())

    if connector_ui:
        redirect_urls = [CONNECTOR_UI_REDIRECT_URL]
        pkce_policy = "NotRequired"
        client_auth_policy = "Required"
        require_client_auth = True
    else:
        redirect_urls = REDIRECT_URLS
        pkce_policy = "Required"
        client_auth_policy = "NotRequiredWhenUsingPKCE"
        require_client_auth = False

    body = {
        "application": {
            "name": client_name,
            "oauthConfiguration": {
                "authorizedRedirectURLs": redirect_urls,
                "authorizedURLValidationPolicy": "AllowWildcards",
                "clientAuthenticationPolicy": client_auth_policy,
                "enabledGrants": ["authorization_code", "refresh_token"],
                "generateRefreshTokens": True,
                "proofKeyForCodeExchangePolicy": pkce_policy,
                "requireClientAuthentication": require_client_auth,
                "scopeHandlingPolicy": "Compatibility",
                "unknownScopePolicy": "Allow",
            },
        }
    }

    resp = requests.post(
        f"{base_url}/api/application/{app_id}",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json=body,
    )

    if resp.status_code in (200, 201):
        app_data = resp.json()["application"]
        result = {
            "name": client_name,
            "client_id": app_data["id"],
        }
        if connector_ui:
            result["client_secret"] = app_data["oauthConfiguration"]["clientSecret"]
        return result
    else:
        print(f"  Failed to create {client_name}: {resp.status_code}")
        return None


def print_mcp_config(client_name: str, client_id: str, mcp_server_url: str, client_secret: str = None):
    """Print the MCP client configuration for the user to add."""
    if client_secret:
        print(f"\n  Connector UI configuration for {client_name}:")
        print(f"  URL:           {mcp_server_url}/mcp")
        print(f"  Client Id:     {client_id}")
        print(f"  Client Secret: {client_secret}")
        print(f"\n  Enter these values in Settings -> Connectors in Claude Desktop or claude.ai.")
        return

    args = ["mcp-remote", f"{mcp_server_url}/mcp"]
    if mcp_server_url.startswith("http://"):
        args.append("--allow-http")
    args += ["--static-oauth-client-info", f'{{"client_id":"{client_id}"}}']

    config = {
        "mcpServers": {
            "fusionauth-mcp": {
                "command": "npx",
                "args": args,
            }
        }
    }

    print(f"\n  MCP configuration for {client_name}:")
    print(f"  Client Id: {client_id}")
    print(f"\n  Add this to your MCP client config:")
    print(f"  {json.dumps(config, indent=2)}")


def main():
    parser = argparse.ArgumentParser(description="Set up an MCP client in FusionAuth")
    parser.add_argument(
        "--fusionauth-url",
        default=FUSIONAUTH_URL,
        help=f"FusionAuth URL (default: {FUSIONAUTH_URL})",
    )
    parser.add_argument(
        "--api-key",
        default=API_KEY,
        help="FusionAuth API key",
    )
    parser.add_argument(
        "--mcp-server-url",
        default="http://localhost:8000",
        help="MCP server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--connector-ui",
        action="store_true",
        help="Register for the Claude Desktop or claude.ai connector UI (uses https://claude.ai/api/mcp/auth_callback as redirect URL and outputs client secret)",
    )
    args = parser.parse_args()

    print("FusionAuth MCP Client Setup")
    print("=" * 40)

    print(f"\nChecking FusionAuth at {args.fusionauth_url}...")
    if not check_fusionauth(args.fusionauth_url, args.api_key):
        print("Error: Cannot connect to FusionAuth. Is it running?")
        print(f"  URL: {args.fusionauth_url}")
        print("  Run 'docker compose up -d' first.")
        sys.exit(1)
    print("FusionAuth is running.")

    # Try to create the custom scope on the MCP Server application
    print("\nConfiguring MCP Server application scope...")
    create_scope(args.fusionauth_url, args.api_key, MCP_SERVER_APP_ID)

    client_name = input("\nEnter a name for this MCP client (e.g. Claude Desktop): ").strip()
    if not client_name:
        print("No name provided. Exiting.")
        sys.exit(0)

    print(f"\n  Creating {client_name}...")
    result = create_client_application(args.fusionauth_url, args.api_key, client_name, args.connector_ui)

    if result:
        print(f"  Created {result['name']} (Client Id: {result['client_id']})")
        print("\n" + "=" * 40)
        print("Setup complete!")
        print("=" * 40)
        print_mcp_config(result["name"], result["client_id"], args.mcp_server_url, result.get("client_secret"))

        print("\n\nTest user credentials:")
        print("  Email: test@example.com")
        print("  Password: password")
    else:
        print("\nClient was not created.")


if __name__ == "__main__":
    main()
