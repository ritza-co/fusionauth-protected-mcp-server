# FusionAuth MCP Server Tutorial

A complete example of protecting an MCP (Model Context Protocol) server with FusionAuth OAuth.

## What This Demo Shows

- MCP server with a single `get_name` tool protected by OAuth
- FusionAuth as the OAuth authorization server
- Custom OAuth scope (`get_name`) with user consent
- Token validation via UserInfo endpoint
- Complete Docker Compose setup with kickstart configuration
- Claude Desktop integration via mcp-remote

## Prerequisites

- **Node.js >= 20.18.1**
- **Docker Desktop**
- **Claude Desktop**
- **Python 3.12+**
- **FusionAuth Enterprise license** - Custom OAuth scopes require an Enterprise license. [Contact FusionAuth](https://fusionauth.io/pricing) to obtain a license key.

## Quick Start

### 1. Configure your license

Open `kickstart/kickstart.json` and replace `YOUR_LICENSE_KEY_HERE` with your FusionAuth Enterprise license key.

### 2. Start the stack

```bash
docker compose up -d
```

Wait about 30 seconds for all services to be healthy.

### 3. Register Claude Desktop as a client

```bash
cd setup
pip install -r requirements.txt
python setup_clients.py
```

Copy the client ID that's printed.

### 4. Configure Claude Desktop

Open Claude Desktop and go to **Settings → Developer → Edit Config**.

Add this configuration (replace `YOUR_CLIENT_ID_HERE` with the client ID from step 3):

```json
{
  "mcpServers": {
    "fusionauth-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--allow-http",
        "--static-oauth-client-info",
        "{\"client_id\":\"YOUR_CLIENT_ID_HERE\"}"
      ]
    }
  }
}
```

### 5. Test the connection

Restart Claude Desktop. Your browser will open to FusionAuth's login page.

Login credentials:
- Email: `test@example.com`
- Password: `password`

After granting consent, ask Claude: "What's my name?"

## Branches

- **main** - Starter code (unprotected MCP server) - follow the tutorial to add OAuth
- **completed-app** - Complete implementation with OAuth protection

## Architecture

- **FusionAuth** (port 9011) - OAuth authorization server
- **MCP Server** (port 8000) - Protected MCP server with `get_name` tool
- **PostgreSQL** - FusionAuth database
- **OpenSearch** - FusionAuth search engine

## Learn More

See the full tutorial at [FusionAuth Documentation](https://fusionauth.io/docs) (link TBD)
