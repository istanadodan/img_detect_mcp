"""MCP server entry point for module execution."""

import asyncio
import sys
from mcp_server.settings import settings
import logging

logger = logging.getLogger(__name__)

try:
    if settings.mcp_server_type.lower() == "fastmcp":
        # Use FastMCP-based server
        from mcp_server.fastmcp_server import run_server

        run_server()
    else:
        # Use MCP SDK-based server (default)
        from mcp_server.server import run_server

        asyncio.run(run_server())
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
