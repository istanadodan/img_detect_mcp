"""FastAPI application with MCP server info."""

import logging

from fastapi import FastAPI

from .logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="FastAPI-based MCP server with YOLOv8 image analysis",
    version="0.1.0",
)

logger.info("FastAPI app initialized")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


@app.get("/info", tags=["info"])
async def info() -> dict[str, str]:
    """Server information."""
    logger.debug("Info endpoint called")
    return {
        "name": "mcp-api-server",
        "version": "0.1.0",
        "protocol": "MCP (Model Context Protocol)",
        "transport": "stdio",
        "description": "YOLOv8-based image analysis with embedding integration",
    }
