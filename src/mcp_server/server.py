"""MCP Server instance and StdIO runner."""

from mcp.server import InitializationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities
from mcp_server.settings import settings
from mcp_server.tools import analyze_image
from mcp_server.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Create MCP server instance
server = Server(settings.mcp_server_name, version="0.1.0")
logger.info(f"MCP server '{settings.mcp_server_name}' (v0.1.0) created")


async def run_server() -> None:
    """Run MCP server with stdio transport."""
    setup_logging(use_console=False)
    logger.info("Starting MCP server with stdio transport")

    # Register tool handlers
    from mcp_server.tools import list_tools

    server.list_tools()(list_tools)
    server.call_tool()(analyze_image)
    logger.info("All tools registered")

    init_options = InitializationOptions(
        server_name=settings.mcp_server_name,
        server_version="0.1.0",
        capabilities=ServerCapabilities(),
    )

    try:
        async with stdio_server() as streams:
            read_stream, write_stream = streams
            await server.run(
                read_stream, write_stream, init_options, raise_exceptions=True
            )
    except KeyboardInterrupt:
        logger.info("MCP server interrupted by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("MCP server shutdown")
