"""FastMCP-based MCP server for stdio transport."""

from fastmcp import FastMCP
from mcp_server.settings import settings
from mcp_server.tools import analyze_image_impl
from mcp_server.utils.logging_config import get_logger, setup_logging

setup_logging(use_console=False)

logger = get_logger(__name__)


async def wrapper(x):
    result = await analyze_image_impl(x)
    return result.model_dump_json()


# Create FastMCP app
fastmcp = FastMCP(settings.mcp_server_name, version="0.1.0")
fastmcp.add_tool(wrapper)


# @fastmcp.tool()
# async def analyze_image(image_path: str, conf_threshold: float | None = None) -> str:
#     """
#     Analyze an image using YOLOv8 object detection and embed detected objects.

#     Args:
#         image_path: Absolute path to image file (PNG/JPEG)
#         conf_threshold: Detection confidence threshold (0-1), defaults to config value

#     Returns:
#         JSON string with analysis results
#     """
#     result = await analyze_image_impl(image_path, conf_threshold)
#     return result.model_dump_json()


def run_server() -> None:
    """Run FastMCP server with stdio transport."""
    logger.info("Starting FastMCP server with stdio transport")
    logger.info("YOLOv8 model will be loaded on first request")

    try:
        # FastMCP 공식 방식: app.run()으로 실행
        # print(asyncio.run(fastmcp.list_tools()))
        fastmcp.run(transport="stdio", show_banner=False)
    except KeyboardInterrupt:
        logger.info("FastMCP server interrupted by user")
    except Exception as e:
        logger.error(f"FastMCP server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("FastMCP server shutdown")


if __name__ == "__main__":
    run_server()
