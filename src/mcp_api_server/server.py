"""MCP Server instance definition."""

from mcp.server import Server

from .config import settings

mcp_server = Server(settings.mcp_server_name)


def register_tools() -> None:
    """Register all MCP tools."""
    # Import to trigger tool registration decorators
    from . import tools  # noqa: F401
