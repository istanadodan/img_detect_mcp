"""YOLOv8 image analysis tool with embedding integration."""

import base64
import io
import os
from pathlib import Path

import httpx
from mcp.types import Tool
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
        # Set YOLO_HOME to project-relative models directory
        yolo_home = Path(settings.yolo_home).resolve()
        yolo_home.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading YOLOv8 model: {settings.yolo_model}")
        logger.info(f"Model cache directory: {yolo_home}")

        # Change to yolo_home directory to load/save model there
        original_cwd = os.getcwd()
        try:
            os.chdir(yolo_home)
            _yolo_model = YOLO(settings.yolo_model)
        finally:
            os.chdir(original_cwd)

        # Verify model file location
        model_path = yolo_home / settings.yolo_model
        if model_path.exists():
            logger.info(f"Model saved at: {model_path}")
        else:
            logger.warning(f"Model not found at expected location: {model_path}")

        logger.info("YOLOv8 model loaded successfully")
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
    image_path: str,
    conf_threshold: float | None = None,
) -> AnalysisResult:
    """
    Analyze image with YOLOv8 and get embeddings for detected objects.

    Args:
        image_path: Absolute path to image file (PNG/JPEG)
        conf_threshold: Detection confidence threshold (overrides config if set)

    Returns:
        AnalysisResult containing list of detections with embeddings
    """
    logger.info(f"Starting image analysis from: {image_path}")

    # Load and resize image
    try:
        image = Image.open(image_path).convert("RGB")
        original_size = image.size

        # Resize to 1024x1024
        image_resized = image.resize((1024, 1024), Image.Resampling.LANCZOS)
        logger.debug(f"Image loaded: {original_size}, resized to: {image_resized.size}")
    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        raise

    # Run YOLOv8 on resized image
    model = _get_yolo_model()
    conf = (
        conf_threshold if conf_threshold is not None else settings.yolo_conf_threshold
    )
    logger.debug(f"Running YOLOv8 detection with confidence threshold: {conf}")
    results = model.predict(image_resized, conf=conf, verbose=False)

    detections: list[Detection] = []

    if results and len(results) > 0:
        result = results[0]
        boxes = result.boxes
        if boxes is not None:
            logger.info(f"Detected {len(boxes)} objects")

            for i in range(len(boxes)):
                class_id = int(boxes.cls[i])
                class_name = str(model.names[class_id])
                confidence = float(boxes.conf[i])
                bbox = boxes.xyxy[i].tolist()

                logger.debug(
                    f"Object {i+1}: {class_name} (confidence: {confidence:.2f})"
                )

                # Crop and embed from resized image
                crop_b64 = _crop_image_to_base64(image_resized, bbox)

                embedding: list[float] | None = None
                try:
                    embedding = await _get_embedding(crop_b64)
                except Exception as e:
                    # If embedding API fails, use default zero vector
                    embedding_dim = 10  # CLIP model default dimension
                    embedding = [0.0] * embedding_dim
                    logger.warning(
                        f"Failed to get embedding for {class_name}: {e}. "
                        f"Using default zero vector ({embedding_dim} dimensions)"
                    )

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


async def analyze_image(name: str, arguments: dict) -> str:
    """
    Analyze an image using YOLOv8 and embed detected objects.

    Args:
        image_path: Absolute path to image file (PNG/JPEG)
        conf_threshold: Detection confidence threshold (0-1, optional)

    Returns:
        JSON string with detection results
    """
    if name != "analyze_image":
        logger.error(f"Unexpected tool name: {name}")
        raise ValueError(f"Unexpected tool name: {name}")

    image_path: str = arguments.get("image_path", "")
    if not image_path:
        raise ValueError("image_path is required")
    conf_threshold: float | None = arguments.get("conf_threshold")

    logger.info(f"analyze_image tool called. path={image_path}")
    result = await analyze_image_impl(image_path, conf_threshold)
    return result.model_dump_json()


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
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to image file (PNG/JPEG format)",
                    },
                    "conf_threshold": {
                        "type": "number",
                        "description": "Detection confidence threshold (0-1), "
                        f"defaults to {settings.yolo_conf_threshold}",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["image_path"],
            },
        ),
    ]


def register_image_analysis_tool() -> None:
    """Register image analysis tool handlers."""
    # Pre-load YOLOv8 model during tool registration
    logger.info("Pre-loading YOLOv8 model...")
    _get_yolo_model()

    # Register tool handlers explicitly
    mcp_server.call_tool()(analyze_image)  # type: ignore
    mcp_server.list_tools()(list_tools)  # type: ignore
    logger.info("Image analysis tool registered")
