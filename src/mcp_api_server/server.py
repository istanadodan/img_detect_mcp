"""MCP Server instance definition."""

from mcp.server import Server

from .config import settings

# Create MCP server instance
mcp_server = Server(settings.mcp_server_name)


async def register_tools() -> None:
    """Register all MCP tools by importing tool modules."""
    # Import modules to trigger tool registration decorators
    from . import tools  # noqa: F401
