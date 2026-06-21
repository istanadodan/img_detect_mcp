"""MCP server CLI for stdio-based operation."""

from mcp.server import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities

from .config import settings
from .logging_config import get_logger, setup_logging
from .server import mcp_server, register_tools

logger = get_logger(__name__)


async def main() -> None:
    """Run MCP server with stdio transport."""
    setup_logging(use_console=False)
    logger.info("Starting MCP server with stdio transport")

    await register_tools()
    logger.info("All tools registered")

    init_options = InitializationOptions(
        server_name=settings.mcp_server_name,
        server_version="0.1.0",
        capabilities=ServerCapabilities(),
    )

    try:
        async with stdio_server() as streams:
            read_stream, write_stream = streams
            await mcp_server.run(read_stream, write_stream, init_options, raise_exceptions=True)
    except KeyboardInterrupt:
        logger.info("MCP server interrupted by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("MCP server shutdown")
