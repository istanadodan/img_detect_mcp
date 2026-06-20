"""MCP server CLI for stdio-based operation."""

import asyncio

from mcp.server.stdio import stdio_server

from .logging_config import get_logger, setup_logging
from .server import mcp_server, register_tools

logger = get_logger(__name__)


async def main() -> None:
    """Run MCP server with stdio transport."""
    # Setup logging first
    setup_logging()
    logger.info("Starting MCP server with stdio transport")

    # Register tools
    await register_tools()
    logger.info("All tools registered, starting server...")

    # Create an event to keep the server running
    stop_event = asyncio.Event()

    # Run with stdio
    try:
        async with stdio_server(mcp_server):
            logger.info("MCP server running and listening on stdio")
            # Wait until interrupted
            await stop_event.wait()
    except KeyboardInterrupt:
        logger.info("MCP server interrupted by user")
    except Exception as e:
        logger.error(f"Error in MCP server: {e}", exc_info=True)
        raise
