"""YOLOv8 image analysis tool with embedding integration."""

import base64
import io
import json
import logging

import httpx
from mcp.types import TextContent, Tool
from PIL import Image
from ultralytics import YOLO

from ..config import settings
from ..logging_config import get_logger
from ..models import AnalysisResult, Detection
from ..server import mcp_server

logger = get_logger(__name__)

# Global YOLO model instance (lazy loaded)
_yolo_model: YOLO | None = None


def _get_yolo_model() -> YOLO:
    """Load YOLOv8 model (lazy loading)."""
    global _yolo_model
    if _yolo_model is None:
        logger.info(f"Loading YOLOv8 model: {settings.yolo_model}")
        _yolo_model = YOLO(settings.yolo_model)
        logger.info(f"YOLOv8 model loaded successfully")
    return _yolo_model


async def _get_embedding(image_base64: str) -> list[float]:
    """
    Get embedding for an image by calling external embedding API.

    Args:
        image_base64: Base64-encoded image data

    Returns:
        Embedding vector as list of floats

    Raises:
        httpx.HTTPError: If embedding API call fails
        json.JSONDecodeError: If response is invalid JSON
    """
    logger.debug(f"Requesting embedding from {settings.embedding_host}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.embedding_host}/embeddings",
            json={
                "model": settings.embedding_model,
                "input": [image_base64],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    embedding: list[float] = data["data"][0]["embedding"]
    logger.debug(f"Embedding obtained: {len(embedding)} dimensions")
    return embedding


def _crop_image_to_base64(image: Image.Image, bbox: list[float]) -> str:
    """
    Crop image to bounding box and encode as base64.

    Args:
        image: PIL Image
        bbox: [x1, y1, x2, y2] in pixel coordinates

    Returns:
        Base64-encoded cropped image
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    cropped = image.crop((x1, y1, x2, y2))

    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


async def analyze_image_impl(
    image_base64: str,
    conf_threshold: float | None = None,
) -> AnalysisResult:
    """
    Analyze image with YOLOv8 and get embeddings for detected objects.

    Args:
        image_base64: Base64-encoded image (PNG/JPEG)
        conf_threshold: Detection confidence threshold (overrides config if set)

    Returns:
        AnalysisResult containing list of detections with embeddings
    """
    logger.info("Starting image analysis")
    # Decode image
    try:
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logger.debug(f"Image decoded: {image.size}")
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        raise

    # Run YOLOv8
    model = _get_yolo_model()
    conf = conf_threshold if conf_threshold is not None else settings.yolo_conf_threshold
    logger.debug(f"Running YOLOv8 detection with confidence threshold: {conf}")
    results = model.predict(image, conf=conf, verbose=False)

    detections: list[Detection] = []

    if results and len(results) > 0:
        result = results[0]
        boxes = result.boxes
        logger.info(f"Detected {len(boxes)} objects")

        for i, box in enumerate(boxes):
            class_id = int(box.cls[0])
            class_name = str(model.names[class_id])
            confidence = float(box.conf[0])
            bbox = box.xyxy[0].tolist()

            logger.debug(f"Object {i+1}: {class_name} (confidence: {confidence:.2f})")

            # Crop and embed
            crop_b64 = _crop_image_to_base64(image, bbox)

            embedding: list[float] | None = None
            try:
                embedding = await _get_embedding(crop_b64)
            except Exception as e:
                # If embedding fails, include null and continue
                logger.warning(f"Failed to get embedding for {class_name}: {e}")

            detection = Detection(
                class_name=class_name,
                confidence=confidence,
                bbox=bbox,
                embedding=embedding,
            )
            detections.append(detection)
    else:
        logger.info("No objects detected in image")

    result = AnalysisResult(detections=detections, total_objects=len(detections))
    logger.info(f"Image analysis complete: {len(detections)} detections")
    return result


@mcp_server.call_tool()
async def analyze_image(
    image_base64: str,
    conf_threshold: float | None = None,
) -> TextContent:
    """
    Analyze an image using YOLOv8 and embed detected objects.

    Args:
        image_base64: Base64-encoded image (PNG/JPEG)
        conf_threshold: Detection confidence threshold (0-1, optional)

    Returns:
        MCP TextContent with JSON array of detections
    """
    logger.info("analyze_image tool called")
    result = await analyze_image_impl(image_base64, conf_threshold)
    return TextContent(type="text", text=result.model_dump_json())


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    logger.debug("list_tools called")
    return [
        Tool(
            name="analyze_image",
            description=(
                "Analyze an image using YOLOv8 object detection and embed detected objects "
                "via external API. Returns list of detections with class names, confidence "
                "scores, bounding boxes, and embedding vectors."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "Base64-encoded image (PNG/JPEG format)",
                    },
                    "conf_threshold": {
                        "type": "number",
                        "description": "Detection confidence threshold (0-1), "
                        f"defaults to {settings.yolo_conf_threshold}",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["image_base64"],
            },
        ),
    ]


def register_image_analysis_tool() -> None:
    """Register image analysis tool handlers."""
    # Handlers are registered via decorators above
    pass
