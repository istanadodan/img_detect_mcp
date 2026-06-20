"""Tests for Pydantic models."""

import pytest

from src.mcp_api_server.models import AnalysisResult, Detection


def test_detection_model_valid() -> None:
    """Test Detection model with valid data."""
    detection = Detection(
        class_name="person",
        confidence=0.95,
        bbox=[100.0, 50.0, 200.0, 300.0],
        embedding=[0.1, 0.2, 0.3],
    )
    assert detection.class_name == "person"
    assert detection.confidence == 0.95
    assert len(detection.bbox) == 4
    assert detection.embedding is not None
    assert len(detection.embedding) == 3


def test_detection_model_no_embedding() -> None:
    """Test Detection model with None embedding."""
    detection = Detection(
        class_name="cat",
        confidence=0.85,
        bbox=[10.0, 20.0, 30.0, 40.0],
        embedding=None,
    )
    assert detection.embedding is None


def test_detection_model_invalid_confidence() -> None:
    """Test Detection model rejects invalid confidence values."""
    with pytest.raises(ValueError):
        Detection(
            class_name="dog",
            confidence=1.5,  # Out of range
            bbox=[0.0, 0.0, 1.0, 1.0],
            embedding=None,
        )


def test_analysis_result_model() -> None:
    """Test AnalysisResult model."""
    detections = [
        Detection(
            class_name="person",
            confidence=0.9,
            bbox=[10.0, 20.0, 30.0, 40.0],
        ),
        Detection(
            class_name="cat",
            confidence=0.8,
            bbox=[50.0, 60.0, 70.0, 80.0],
        ),
    ]
    result = AnalysisResult(detections=detections, total_objects=2)
    assert result.total_objects == 2
    assert len(result.detections) == 2
    assert result.detections[0].class_name == "person"


def test_analysis_result_json_serialization() -> None:
    """Test AnalysisResult JSON serialization."""
    detection = Detection(
        class_name="person",
        confidence=0.9,
        bbox=[10.0, 20.0, 30.0, 40.0],
    )
    result = AnalysisResult(detections=[detection], total_objects=1)

    json_str = result.model_dump_json()
    assert isinstance(json_str, str)
    assert "person" in json_str
    assert "0.9" in json_str
