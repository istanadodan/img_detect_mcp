"""FastAPI application with MCP server integration."""

from fastapi import FastAPI
from mcp.server.fastapi import create_mcp_router

from .server import mcp_server, register_tools

# Register all MCP tools
register_tools()

# Create FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="FastAPI-based MCP server with YOLOv8 image analysis",
    version="0.1.0",
)

# Mount MCP router
app.include_router(create_mcp_router(mcp_server), prefix="/mcp")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
