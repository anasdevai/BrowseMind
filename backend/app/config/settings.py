"""
Configuration management for BrowserMind backend.
Loads environment variables and provides typed configuration objects.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database Configuration
    database_url: str = "sqlite:///./browsermind.db"
    database_encryption_key: str

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"

    # WebSocket Configuration
    ws_heartbeat_interval: int = 30
    ws_timeout: int = 30
    ws_max_connections: int = 100
    ws_rate_limit: int = 100

    # Security
    cors_origins: List[str] = ["http://localhost:3000", "chrome-extension://*"]
    secret_key: str

    # Feature Flags
    enable_cleanup_job: bool = True
    cleanup_interval_hours: int = 24
    session_retention_days: int = 90

    @property
    def database_path(self) -> str:
        """Extract database file path from database URL."""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return "browsermind.db"


# Global settings instance
settings = Settings()
