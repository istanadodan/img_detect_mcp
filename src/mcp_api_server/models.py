"""Pydantic data models for type safety and validation."""

from pydantic import BaseModel, Field


class Detection(BaseModel):
    """Single object detection result."""

    class_name: str = Field(..., description="Detected object class name")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score (0-1)",
    )
    bbox: list[float] = Field(
        ...,
        description="Bounding box coordinates [x1, y1, x2, y2]",
    )
    embedding: list[float] | None = Field(
        None,
        description="Embedding vector from external API (None if failed)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "class_name": "person",
                "confidence": 0.91,
                "bbox": [100.0, 50.0, 200.0, 300.0],
                "embedding": [0.12, -0.34, 0.56],
            }
        }


class AnalysisResult(BaseModel):
    """Complete image analysis result."""

    detections: list[Detection] = Field(
        ...,
        description="List of detected objects",
    )
    total_objects: int = Field(
        ...,
        ge=0,
        description="Total number of detections",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detections": [
                    {
                        "class_name": "person",
                        "confidence": 0.91,
                        "bbox": [100.0, 50.0, 200.0, 300.0],
                        "embedding": [0.12, -0.34, 0.56],
                    }
                ],
                "total_objects": 1,
            }
        }
