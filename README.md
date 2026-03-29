# ExposureGuard MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that connects AI assistants to the [ExposureGuard](https://getexposureguard.com) domain security scanning API.

## Tools

| Tool | Description |
|------|-------------|
| `scan_domain` | Full security scan — 8 checks, A-F grade, score, findings, report URL (~8s) |
| `get_grade` | Cached grade lookup (up to 24h old) — fast, no new scan triggered |
| `get_remediation` | Copy-paste fix snippets for all failing checks |
| `get_dependencies` | Third-party scripts/resources loaded by the domain |

## Setup

### 1. Get an API Key

Sign up at [getexposureguard.com](https://getexposureguard.com) and grab your API key from the [dashboard](https://getexposureguard.com/dashboard/api-keys).

### 2. Install

```bash
# Option A: pip install (recommended)
pip install -e /path/to/exposureguard-mcp

# Option B: just install deps
pip install mcp httpx
```

### 3. Configure Your AI Client

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "exposureguard": {
      "command": "python",
      "args": ["-m", "exposureguard_mcp.server"],
      "env": {
        "EXPOSUREGUARD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

If you installed as a package, you can also use:

```json
{
  "mcpServers": {
    "exposureguard": {
      "command": "exposureguard-mcp",
      "env": {
        "EXPOSUREGUARD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Cursor

Edit `.cursor/mcp.json` in your project root (or globally at `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "exposureguard": {
      "command": "python",
      "args": ["-m", "exposureguard_mcp.server"],
      "env": {
        "EXPOSUREGUARD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "exposureguard": {
      "command": "python",
      "args": ["-m", "exposureguard_mcp.server"],
      "env": {
        "EXPOSUREGUARD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### VS Code (Copilot)

Edit `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "exposureguard": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "exposureguard_mcp.server"],
      "env": {
        "EXPOSUREGUARD_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 4. Usage Examples

Once connected, ask your AI assistant:

- "Scan example.com for security issues"
- "What's the security grade for cloudflare.com?"
- "Show me how to fix the security issues on my-site.com"
- "What third-party scripts does shopify.com load?"

## Running Standalone

```bash
export EXPOSUREGUARD_API_KEY=your-api-key-here
python -m exposureguard_mcp.server
```

The server communicates over stdio using the MCP protocol — it's designed to be launched by an MCP client, not used interactively.

## Rate Limits

Rate limits depend on your ExposureGuard plan. If you hit a 429 response, the server will return a message suggesting you upgrade at [getexposureguard.com/pricing](https://getexposureguard.com/pricing).

## Publishing

### PyPI
```bash
pip install build twine
python -m build
twine upload dist/*
```
Then users install with: `pip install exposureguard-mcp`

### npm
```bash
npm publish
```
Then users install with: `npx exposureguard-mcp`

## License

MIT
