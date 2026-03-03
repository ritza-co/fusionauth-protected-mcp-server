# FusionAuth MCP Server Tutorial

A step-by-step tutorial for protecting an MCP (Model Context Protocol) server with FusionAuth OAuth.

## Tutorial Structure

This repository supports a hands-on tutorial where you'll add OAuth protection to an MCP server:

- **Start here (main branch)**: Unprotected MCP server with a simple `get_name` tool
- **Follow the tutorial**: Add OAuth protection step-by-step
- **Reference (completed-app branch)**: Complete working implementation

The tutorial walks you through adding:
- FusionAuth OAuth configuration
- Token validation via UserInfo endpoint
- Custom scopes and consent flow
- Client registration

To see the completed implementation:
```bash
git checkout completed-app
```

## Prerequisites

- Node.js >= 20.18.1
- Docker Desktop
- Claude Desktop
- Python 3.12+
- **FusionAuth Enterprise license** - Custom OAuth scopes require an Enterprise license. [Contact FusionAuth](https://fusionauth.io/pricing) to obtain a license key.

## Quick Start (Starter Code)

This starter code gives you a working MCP server without authentication. You'll add OAuth protection as you follow the tutorial.

### 1. Configure your license

Open `kickstart/kickstart.json` and replace `YOUR_LICENSE_KEY_HERE` with your FusionAuth Enterprise license key.

### 2. Start the Docker stack

```bash
docker compose up -d
```

Wait about 30 seconds for all services to start. This includes:
- FusionAuth (port 9011) - pre-configured via kickstart
- MCP Server (port 8000) - unprotected starter version
- PostgreSQL - FusionAuth database
- OpenSearch - FusionAuth search engine

### 3. Test the unprotected server

The MCP server is running but has no authentication. You can test it directly:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_name",
      "arguments": {}
    }
  }'
```

You should see:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello, World!"
      }
    ]
  }
}
```

### 4. Follow the tutorial

Now you're ready to add OAuth protection! Follow the tutorial to:
- Add token validation
- Register Claude Desktop as a client
- Test the protected server

## Learn More

See the full tutorial at [FusionAuth Documentation](https://fusionauth.io/docs) (link TBD)
