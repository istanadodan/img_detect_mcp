"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    embedding_host: str = "http://192.168.0.100:7997"
    embedding_model: str = "openai/clip-vit-large-patch14"
    yolo_model: str = "yolov8n.pt"
    yolo_conf_threshold: float = 0.5
    mcp_server_name: str = "mcp-api-server"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
