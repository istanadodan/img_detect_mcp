"""Configuration management using Pydantic Settings."""

import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Log configuration after loading
_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        arbitrary_types_allowed=True,
    )

    embedding_host: str = "http://192.168.0.100:7997"
    embedding_model: str = "openai/clip-vit-large-patch14"
    yolo_model: str = "yolov8n.pt"
    yolo_home: str = "./models"
    yolo_conf_threshold: float = 0.5
    mcp_server_name: str = "mcp-api-server"
    log_level: str = "INFO"
    mcp_server_type: str = "fastmcp"  # "sdk" or "fastmcp"

    @staticmethod
    def get_project_root() -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent


settings = Settings()


if Path(".env").exists():
    _logger.debug("Configuration loaded from .env file")
else:
    _logger.debug("Configuration loaded from environment variables")

_logger.debug(f"Embedding server: {settings.embedding_host}")
_logger.debug(f"YOLOv8 model: {settings.yolo_model}")
_logger.debug(f"Confidence threshold: {settings.yolo_conf_threshold}")
