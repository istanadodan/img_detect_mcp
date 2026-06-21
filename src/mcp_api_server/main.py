"""FastAPI application with HTTP/SSE-based MCP server integration."""

import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse

from .config import settings
from .logging_config import setup_logging
from .server import register_tools

# Setup logging (with console output for FastAPI)
setup_logging(use_console=True)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager."""
    # Startup
    logger.info("Registering MCP tools on startup...")
    await register_tools()
    logger.info("MCP tools registered successfully")
    yield
    # Shutdown
    logger.info("Shutting down MCP server")


# Create FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="FastAPI-based MCP server with HTTP/SSE transport and YOLOv8 image analysis",
    version="0.1.0",
    lifespan=lifespan,
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
        "name": settings.mcp_server_name,
        "version": "0.1.0",
        "protocol": "MCP (Model Context Protocol)",
        "transport": "HTTP/SSE and WebSocket",
        "description": "YOLOv8-based image analysis with embedding integration",
    }


@app.post("/mcp/messages", tags=["mcp"])
async def handle_mcp_message(request: Request) -> JSONResponse:
    """
    Handle MCP JSON-RPC 2.0 messages via HTTP POST.

    This endpoint accepts JSON-RPC requests and returns JSON-RPC responses.
    Supports all standard MCP operations (initialize, call_tool, etc).
    """
    logger.debug("MCP HTTP message received")

    try:
        body = await request.json()
        logger.debug(f"MCP request: {body.get('method', 'unknown')}")

        # Process the message through MCP server
        # Since we're using the MCP server directly, we need to call its methods
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        result: dict[str, Any] | None = None
        error: dict[str, Any] | None = None

        try:
            # Handle different MCP methods
            if method == "initialize":
                # Initialize request
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {
                        "name": settings.mcp_server_name,
                        "version": "0.1.0",
                    },
                }
                logger.info("MCP server initialized")

            elif method == "tools/list":
                # List available tools
                from .tools.image_analysis import list_tools

                tools = await list_tools()
                result = {"tools": [tool.model_dump() for tool in tools]}
                logger.debug(f"Listed {len(tools)} tools")

            elif method == "tools/call":
                # Call a tool
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if tool_name == "analyze_image":
                    from .tools.image_analysis import analyze_image_impl

                    image_b64: str = tool_args.get("image_base64", "")
                    conf_threshold: float | None = tool_args.get("conf_threshold")
                    analysis_result = await analyze_image_impl(image_b64, conf_threshold)
                    result = {
                        "type": "text",
                        "text": analysis_result.model_dump_json(),
                    }
                    logger.info(f"Tool '{tool_name}' executed successfully")
                else:
                    error = {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}",
                    }
                    logger.warning(f"Unknown tool requested: {tool_name}")

            else:
                error = {
                    "code": -32601,
                    "message": f"Unknown method: {method}",
                }
                logger.warning(f"Unknown MCP method: {method}")

        except Exception as e:
            error = {
                "code": -32603,
                "message": f"Internal error: {str(e)}",
            }
            logger.error(f"Error processing MCP request: {e}", exc_info=True)

        # Build JSON-RPC response
        response: dict[str, Any] = {
            "jsonrpc": "2.0",
        }
        if request_id is not None:
            response["id"] = request_id

        if error:
            response["error"] = error
        else:
            response["result"] = result

        logger.debug("MCP response prepared")
        return JSONResponse(content=response)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in MCP request: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                },
            },
        )
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                },
            },
        )


@app.websocket("/mcp/ws")
async def websocket_mcp_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for bidirectional MCP communication.

    Allows persistent, low-latency connection for MCP clients.
    Useful for long-running operations or streaming responses.
    """
    await websocket.accept()
    logger.info("MCP WebSocket connection established")

    try:
        while True:
            # Receive message from client
            message = await websocket.receive_json()
            logger.debug(f"WebSocket MCP message: {message.get('method', 'unknown')}")

            # Process message (similar to HTTP endpoint)
            method = message.get("method")
            params = message.get("params", {})
            request_id = message.get("id")

            result: dict[str, Any] | None = None
            error: dict[str, Any] | None = None

            try:
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {
                            "name": settings.mcp_server_name,
                            "version": "0.1.0",
                        },
                    }
                    logger.info("MCP initialized via WebSocket")

                elif method == "tools/list":
                    from .tools.image_analysis import list_tools

                    tools = await list_tools()
                    result = {"tools": [tool.model_dump() for tool in tools]}

                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})

                    if tool_name == "analyze_image":
                        from .tools.image_analysis import analyze_image_impl

                        image_b64: str = tool_args.get("image_base64", "")
                        conf_threshold: float | None = tool_args.get("conf_threshold")
                        analysis_result = await analyze_image_impl(image_b64, conf_threshold)
                        result = {
                            "type": "text",
                            "text": analysis_result.model_dump_json(),
                        }
                    else:
                        error = {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}",
                        }

                else:
                    error = {
                        "code": -32601,
                        "message": f"Unknown method: {method}",
                    }

            except Exception as e:
                error = {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                }
                logger.error(f"Error in WebSocket handler: {e}", exc_info=True)

            # Send response
            response: dict[str, Any] = {"jsonrpc": "2.0"}
            if request_id is not None:
                response["id"] = request_id

            if error:
                response["error"] = error
            else:
                response["result"] = result

            await websocket.send_json(response)
            logger.debug("WebSocket response sent")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        logger.info("MCP WebSocket connection closed")
