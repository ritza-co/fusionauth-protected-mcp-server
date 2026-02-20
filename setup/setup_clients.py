#!/usr/bin/env python3
"""
MCP Client Setup Script

Registers MCP clients (Claude Desktop, Cursor, etc.) as OAuth applications
in FusionAuth so they can authenticate against the MCP server.

Usage:
    python setup_clients.py [--fusionauth-url URL] [--api-key KEY]

The script will prompt you to select which clients to register.
"""

import argparse
import json
import sys
import uuid

import requests

FUSIONAUTH_URL = "http://localhost:9011"
API_KEY = "bf69486b-4733-4470-a592-f1bfce7af580"
MCP_SERVER_APP_ID = "e9fdb985-9173-4e01-9d73-ac2d60d1dc8e"

CLIENT_CONFIGS = {
    "claude_desktop": {
        "name": "Claude Desktop",
        "description": "Claude Desktop MCP client",
        "redirect_urls": [
            "http://localhost:3334/oauth/callback",
            "http://127.0.0.1:3334/oauth/callback",
            "http://localhost:3000/callback",
            "http://127.0.0.1:3000/callback",
            "http://localhost:16442/oauth/callback",
            "http://127.0.0.1:16442/oauth/callback",
            "http://localhost/callback",
        ],
    },
    "cursor": {
        "name": "Cursor",
        "description": "Cursor IDE MCP client",
        "redirect_urls": [
            "http://localhost:3000/callback",
            "http://127.0.0.1:3000/callback",
            "http://localhost/callback",
            "http://localhost:16442/oauth/callback",
            "http://127.0.0.1:16442/oauth/callback",
        ],
    },
}


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
                print("  Note: Custom scopes require a FusionAuth Enterprise license.")
                print("  The MCP server will still work, but without the custom 'get_name' scope.")
                return False
        print(f"  Failed to create scope: {resp.status_code}")
        return False
    else:
        print(f"  Failed to create scope: {resp.status_code}")
        return False


def create_client_application(
    base_url: str, api_key: str, client_key: str, config: dict
) -> dict | None:
    """Create an OAuth application in FusionAuth for an MCP client."""
    app_id = str(uuid.uuid4())

    body = {
        "application": {
            "name": config["name"],
            "oauthConfiguration": {
                "authorizedRedirectURLs": config["redirect_urls"],
                "clientAuthenticationPolicy": "NotRequiredWhenUsingPKCE",
                "enabledGrants": ["authorization_code", "refresh_token"],
                "generateRefreshTokens": True,
                "proofKeyForCodeExchangePolicy": "Required",
                "requireClientAuthentication": False,
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
        return {
            "name": config["name"],
            "client_id": app_data["id"],
            "client_secret": app_data.get("oauthConfiguration", {}).get(
                "clientSecret", ""
            ),
        }
    else:
        print(f"  Failed to create {config['name']}: {resp.status_code}")
        return None


def print_mcp_config(client_name: str, client_id: str, mcp_server_url: str):
    """Print the MCP client configuration for the user to add."""
    config = {
        "mcpServers": {
            "fusionauth-mcp": {
                "command": "npx",
                "args": [
                    "mcp-remote",
                    f"{mcp_server_url}/mcp",
                    "--allow-http",
                    "--static-oauth-client-info",
                    f'{{"client_id":"{client_id}"}}'
                ]
            }
        }
    }

    print(f"\n  MCP configuration for {client_name}:")
    print(f"  Client ID: {client_id}")
    print(f"\n  Add this to your MCP client config:")
    print(f"  {json.dumps(config, indent=2)}")


def main():
    parser = argparse.ArgumentParser(description="Set up MCP clients in FusionAuth")
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

    print("\nAvailable MCP clients:")
    for i, (key, config) in enumerate(CLIENT_CONFIGS.items(), 1):
        print(f"  {i}. {config['name']}")
    print(f"  {len(CLIENT_CONFIGS) + 1}. All")

    choice = input("\nSelect clients to register (comma-separated numbers): ").strip()
    if not choice:
        print("No selection made. Exiting.")
        sys.exit(0)

    selected = []
    keys = list(CLIENT_CONFIGS.keys())
    for num in choice.split(","):
        num = num.strip()
        if num == str(len(CLIENT_CONFIGS) + 1):
            selected = keys[:]
            break
        try:
            idx = int(num) - 1
            if 0 <= idx < len(keys):
                selected.append(keys[idx])
        except ValueError:
            pass

    if not selected:
        print("Invalid selection. Exiting.")
        sys.exit(1)

    print(f"\nRegistering {len(selected)} client(s)...")
    results = []
    for key in selected:
        config = CLIENT_CONFIGS[key]
        print(f"\n  Creating {config['name']}...")
        result = create_client_application(
            args.fusionauth_url, args.api_key, key, config
        )
        if result:
            results.append(result)
            print(f"  Created {result['name']} (Client ID: {result['client_id']})")

    if results:
        print("\n" + "=" * 40)
        print("Setup complete!")
        print("=" * 40)
        for result in results:
            print_mcp_config(
                result["name"], result["client_id"], args.mcp_server_url
            )

        print("\n\nTest user credentials:")
        print("  Email: test@example.com")
        print("  Password: password")

    else:
        print("\nNo clients were created.")


if __name__ == "__main__":
    main()
