"""
ExposureGuard MCP Server

Domain security scanning via the ExposureGuard API.
Exposes tools for scanning domains, checking grades, getting remediation fixes,
and discovering third-party dependencies.

Usage:
    EXPOSUREGUARD_API_KEY=your_key python -m exposureguard_mcp.server
"""

import asyncio
import os
import json
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

API_BASE = "https://getexposureguard.com/api"
POLL_INTERVAL = 2  # seconds
POLL_TIMEOUT = 30  # seconds

server = Server("exposureguard")


def _get_api_key() -> str:
    key = os.environ.get("EXPOSUREGUARD_API_KEY", "")
    if not key:
        raise ValueError(
            "EXPOSUREGUARD_API_KEY environment variable is not set. "
            "Get your API key at https://getexposureguard.com/dashboard/api-keys"
        )
    return key


def _headers() -> dict[str, str]:
    return {
        "X-API-Key": _get_api_key(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _handle_error(response: httpx.Response) -> str | None:
    """Return an error message string if the response indicates failure, else None."""
    if response.status_code == 429:
        return (
            "Rate limit exceeded. You've hit your plan's request limit. "
            "Upgrade your plan at https://getexposureguard.com/pricing for higher limits."
        )
    if response.status_code == 401:
        return "Invalid or expired API key. Check your key at https://getexposureguard.com/dashboard/api-keys"
    if response.status_code == 403:
        return "Access denied. Your plan may not include this endpoint."
    if response.status_code >= 400:
        try:
            body = response.json()
            msg = body.get("error") or body.get("message") or response.text
        except Exception:
            msg = response.text
        return f"API error {response.status_code}: {msg}"
    return None


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="scan_domain",
            description=(
                "Run a full security scan on a domain. Performs 8 checks (SPF, DMARC, DKIM, HTTPS, "
                "SSL certificate, security headers, DNSSEC, open ports) and returns an A-F letter grade, "
                "numeric score 0-100, detailed findings for each check, and a shareable report URL. "
                "Takes ~8 seconds. Use this when you need a fresh, comprehensive security assessment."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain to scan (e.g. 'example.com'). Do not include protocol or path.",
                    }
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="get_grade",
            description=(
                "Get the cached security grade for a domain (up to 24 hours old). Returns the letter grade "
                "(A-F) and numeric score without triggering a new scan. Use this for quick lookups when you "
                "don't need the freshest data — much faster than scan_domain."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain to look up (e.g. 'example.com').",
                    }
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="get_remediation",
            description=(
                "Get copy-paste fix snippets for all failing security checks on a domain. Returns specific "
                "DNS records, server configs, or header values that need to be added or changed. Use this "
                "after a scan to give the user actionable fix instructions they can hand to their DNS provider "
                "or sysadmin."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain to get remediation for (e.g. 'example.com').",
                    }
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="get_dependencies",
            description=(
                "Discover third-party scripts, stylesheets, fonts, and other external resources loaded by a "
                "domain. Useful for supply-chain risk assessment — shows what external services the domain "
                "depends on and could be vulnerable through."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain to analyze (e.g. 'example.com').",
                    }
                },
                "required": ["domain"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "scan_domain":
            return await _scan_domain(arguments["domain"])
        elif name == "get_grade":
            return await _get_grade(arguments["domain"])
        elif name == "get_remediation":
            return await _get_remediation(arguments["domain"])
        elif name == "get_dependencies":
            return await _get_dependencies(arguments["domain"])
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except ValueError as e:
        return [TextContent(type="text", text=str(e))]
    except httpx.ConnectError:
        return [TextContent(type="text", text="Could not connect to ExposureGuard API. Check your network connection.")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def _scan_domain(domain: str) -> list[TextContent]:
    headers = _headers()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{API_BASE}/scan", json={"domain": domain}, headers=headers)
        err = _handle_error(resp)
        if err:
            return [TextContent(type="text", text=err)]

        data = resp.json()

        # Poll if pending
        if data.get("status") == "pending" and data.get("scan_id"):
            scan_id = data["scan_id"]
            elapsed = 0.0
            while elapsed < POLL_TIMEOUT:
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL
                poll_resp = await client.get(f"{API_BASE}/scan-status/{scan_id}", headers=headers)
                poll_err = _handle_error(poll_resp)
                if poll_err:
                    return [TextContent(type="text", text=poll_err)]
                data = poll_resp.json()
                if data.get("status") != "pending":
                    break
            else:
                return [TextContent(type="text", text=(
                    f"Scan timed out after {POLL_TIMEOUT}s. "
                    f"Try again or check https://getexposureguard.com/domain/{domain}"
                ))]

        return [TextContent(type="text", text=json.dumps(data, indent=2))]


async def _get_grade(domain: str) -> list[TextContent]:
    headers = _headers()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}/grade/{domain}", headers=headers)
        err = _handle_error(resp)
        if err:
            return [TextContent(type="text", text=err)]
        return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def _get_remediation(domain: str) -> list[TextContent]:
    headers = _headers()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}/remediation/{domain}", headers=headers)
        err = _handle_error(resp)
        if err:
            return [TextContent(type="text", text=err)]
        return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def _get_dependencies(domain: str) -> list[TextContent]:
    headers = _headers()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}/dependencies/{domain}", headers=headers)
        err = _handle_error(resp)
        if err:
            return [TextContent(type="text", text=err)]
        return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def _run():
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
