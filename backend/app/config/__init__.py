"""
Configuration module for BrowserMind backend.
Exports settings and OpenRouter configuration.
"""
from app.config.settings import Settings, settings
from app.config.openrouter import (
    OpenRouterConfig,
    create_llm_client,
    get_llm_client,
    get_llm_config,
    get_model_name,
)

__all__ = [
    "Settings",
    "settings",
    "OpenRouterConfig",
    "create_llm_client",
    "get_llm_client",
    "get_llm_config",
    "get_model_name",
]
