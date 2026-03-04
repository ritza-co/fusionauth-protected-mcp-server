# FusionAuth Protected MCP Server

Example code for the FusionAuth tutorial: [Protecting MCP Servers With FusionAuth OAuth](https://fusionauth.io/docs/extend/examples/protecting-mcp-servers).

This repository contains three self-contained examples:

| Folder | Description |
|--------|-------------|
| `unprotected-local-mcp/` | Starter code — a simple MCP server with no authentication. Start here if following the tutorial. |
| `protected-local-mcp/` | Completed code — the same MCP server with FusionAuth OAuth protection added. |
| `protected-remote-mcp/` | Remote deployment variant — extends the protected server with flags for deploying to a public URL. |

The `unprotected-local-mcp` and `protected-local-mcp` folders each contain a full Docker stack (FusionAuth, PostgreSQL, MCP server) and can be run independently. The `protected-remote-mcp` folder contains only the MCP server and is intended for use with an existing FusionAuth instance.
