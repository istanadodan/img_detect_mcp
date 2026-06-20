"""Pytest configuration and shared fixtures."""

import base64
import io

import pytest
from PIL import Image


@pytest.fixture
def sample_white_image_base64() -> str:
    """Generate a 100x100 white image encoded as base64."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture
def sample_colored_image_base64() -> str:
    """Generate a 100x100 colored image encoded as base64."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
