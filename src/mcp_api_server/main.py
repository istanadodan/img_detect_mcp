"""FastAPI application with MCP server info."""

from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="FastAPI-based MCP server with YOLOv8 image analysis",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/info", tags=["info"])
async def info() -> dict[str, str]:
    """Server information."""
    return {
        "name": "mcp-api-server",
        "version": "0.1.0",
        "protocol": "MCP (Model Context Protocol)",
        "transport": "stdio",
        "description": "YOLOv8-based image analysis with embedding integration",
    }
