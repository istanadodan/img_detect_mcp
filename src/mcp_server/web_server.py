"""FastAPI application with MCP server integration via HTTP endpoints."""

import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from mcp_server.settings import settings
from mcp_server.utils.logging_config import setup_logging
from mcp_server.fastmcp_server import fastmcp

# Setup logging (with console output for FastAPI)
setup_logging(use_console=True)
logger = logging.getLogger(__name__)

# sub-app
mcp_app = fastmcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager."""
    # Startup
    logger.info("Registering MCP tools on startup...")

    async with mcp_app.lifespan(app):
        logger.info("MCP tools registered successfully")
        yield

    # Shutdown
    logger.info("Shutting down FastAPI server")


# Create FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="FastAPI-based MCP server with YOLOv8 image analysis",
    version="0.1.0",
    lifespan=lifespan,
)

logger.info("FastAPI app initialized")
app.mount("/mcp", mcp_app)


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
        "transport": "HTTP/JSON-RPC 2.0",
        "description": "YOLOv8-based image analysis with embedding integration",
    }


@app.post("/mcp/messages", tags=["mcp"])
async def handle_mcp_message(request: Request) -> JSONResponse:
    """Handle MCP JSON-RPC 2.0 messages via HTTP POST."""
    logger.debug("MCP HTTP message received")

    try:
        body = await request.json()
        logger.debug(f"MCP request: {body.get('method', 'unknown')}")

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

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
                logger.info("MCP server initialized")

            elif method == "tools/list":
                from .tools.image_analysis import list_tools

                tools = await list_tools()
                result = {"tools": [tool.model_dump() for tool in tools]}
                logger.debug(f"Listed {len(tools)} tools")

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if tool_name == "analyze_image":
                    from .tools.image_analysis import analyze_image_impl

                    image_path: str = tool_args.get("image_path", "")
                    conf_threshold: float | None = tool_args.get("conf_threshold")

                    if not image_path:
                        error = {
                            "code": -32602,
                            "message": "Missing required parameter: image_path",
                        }
                    else:
                        analysis_result = await analyze_image_impl(
                            image_path, conf_threshold
                        )
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
        response: dict[str, Any] = {"jsonrpc": "2.0"}
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
    """WebSocket endpoint for bidirectional MCP communication."""
    await websocket.accept()
    logger.info("MCP WebSocket connection established")

    try:
        while True:
            message = await websocket.receive_json()
            logger.debug(f"WebSocket MCP message: {message.get('method', 'unknown')}")

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

                        image_path: str = tool_args.get("image_path", "")
                        conf_threshold: float | None = tool_args.get("conf_threshold")

                        if not image_path:
                            error = {
                                "code": -32602,
                                "message": "Missing required parameter: image_path",
                            }
                        else:
                            analysis_result = await analyze_image_impl(
                                image_path, conf_threshold
                            )
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
