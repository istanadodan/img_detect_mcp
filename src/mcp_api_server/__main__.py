"""MCP server entry point for module execution."""

import asyncio
import logging
import sys

from .logging_config import setup_logging
from .mcp_cli import main

if __name__ == "__main__":
    # Setup logging immediately
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("MCP server starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"MCP server error: {e}", exc_info=True)
        sys.exit(1)
