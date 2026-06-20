"""MCP Server instance definition."""

import logging

from mcp.server import Server

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Create MCP server instance
mcp_server = Server(settings.mcp_server_name)
logger.info(f"MCP server '{settings.mcp_server_name}' created")


async def register_tools() -> None:
    """Register all MCP tools by importing tool modules."""
    logger.info("Registering MCP tools...")
    # Import modules to trigger tool registration decorators
    from . import tools  # noqa: F401
    logger.info("MCP tools registered successfully")
