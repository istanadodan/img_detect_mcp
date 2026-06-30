"""Tests for FastAPI server and health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from mcp_server.web_server import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_info_endpoint() -> None:
    """Test server info endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "mcp-api-server"
        assert data["version"] == "0.1.0"
        assert "MCP" in data["protocol"]
