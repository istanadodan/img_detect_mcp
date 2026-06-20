"""MCP server entry point for module execution."""

import asyncio
import sys

from .mcp_cli import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
