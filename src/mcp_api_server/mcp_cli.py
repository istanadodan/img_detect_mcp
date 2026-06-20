"""MCP server CLI for stdio-based operation."""

import asyncio

from mcp.server.stdio import stdio_server

from .server import mcp_server, register_tools


async def main() -> None:
    """Run MCP server with stdio transport."""
    # Register tools
    await register_tools()

    # Run with stdio
    async with stdio_server(mcp_server) as streams:
        await streams.keep_alive()
