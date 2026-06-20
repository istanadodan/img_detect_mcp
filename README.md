# MCP API Server

FastAPI-based MCP server with YOLOv8 image analysis and embedding integration.

## Features

- **Image Analysis Tool**: Analyze images using YOLOv8 to detect objects
- **Embedding Integration**: Embed detected objects via external API (192.168.0.100:7997)
- **MCP Protocol**: Full Model Context Protocol (MCP) support via FastAPI

## Quick Start

### Prerequisites

- Python 3.12+
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Run the server
uv run uvicorn src.mcp_api_server.main:app --reload
```

### Development

```bash
# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Architecture

- `src/mcp_api_server/main.py` - FastAPI app with MCP router
- `src/mcp_api_server/server.py` - MCP server instance
- `src/mcp_api_server/config.py` - Configuration management
- `src/mcp_api_server/tools/image_analysis.py` - YOLOv8 + embedding tool

## Configuration

See `.env.example` for all available environment variables.

### Embedding Server

By default, images are embedded using an external API at `192.168.0.100:7997`. See [CLAUDE.md](CLAUDE.md) for setup instructions.
