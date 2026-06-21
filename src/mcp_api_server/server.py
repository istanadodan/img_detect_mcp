"""MCP Server instance definition."""


from mcp.server import Server

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Create MCP server instance
mcp_server = Server(settings.mcp_server_name, version="0.1.0")
logger.info(f"MCP server '{settings.mcp_server_name}' (v0.1.0) created")


async def register_tools() -> None:
    """Register all MCP tools by importing tool modules."""
    logger.info("Registering MCP tools...")
    from .tools import register_image_analysis_tool
    register_image_analysis_tool()
    logger.info("MCP tools registered successfully")
