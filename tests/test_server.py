"""Tests for FastAPI server and health endpoint."""

import pytest
from httpx import AsyncClient

from src.mcp_api_server.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_mcp_endpoints_available() -> None:
    """Test that MCP endpoints are mounted."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # MCP router is mounted at /mcp, check it's accessible
        response = await client.get("/mcp/sse", headers={"Accept": "text/event-stream"})
        # Should be either 200 or 400 (invalid request), not 404 (not found)
        assert response.status_code in [200, 400, 405]
