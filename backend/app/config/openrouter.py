"""
OpenRouter client configuration for multi-provider LLM access.
Compatible with OpenAI SDK interface.
"""
from typing import Optional

from openai import AsyncOpenAI
from pydantic_settings import BaseSettings


class OpenRouterConfig(BaseSettings):
    """OpenRouter configuration settings."""

    # OpenRouter API settings
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_app_name: str = "BrowserMind"
    openrouter_app_url: str = "https://github.com/browsermind/browsermind"

    # Model selection
    default_model: str = "anthropic/claude-3.5-sonnet"  # OpenRouter model ID
    fallback_model: str = "openai/gpt-4-turbo-preview"

    # Provider selection (openai or openrouter)
    llm_provider: str = "openrouter"  # "openai" or "openrouter"

    # OpenAI settings (fallback)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # Model parameters
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


def create_llm_client(config: Optional[OpenRouterConfig] = None) -> AsyncOpenAI:
    """
    Create an LLM client (OpenRouter or OpenAI).

    Args:
        config: OpenRouter configuration (uses defaults if None)

    Returns:
        AsyncOpenAI client configured for selected provider
    """
    if config is None:
        config = OpenRouterConfig()

    if config.llm_provider == "openrouter":
        # OpenRouter client (OpenAI-compatible)
        if not config.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        return AsyncOpenAI(
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            default_headers={
                "HTTP-Referer": config.openrouter_app_url,
                "X-Title": config.openrouter_app_name,
            },
            timeout=config.timeout,
        )
    else:
        # OpenAI client
        if not config.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        return AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            timeout=config.timeout,
        )


def get_model_name(config: Optional[OpenRouterConfig] = None) -> str:
    """
    Get the model name for the selected provider.

    Args:
        config: OpenRouter configuration

    Returns:
        Model identifier string
    """
    if config is None:
        config = OpenRouterConfig()

    if config.llm_provider == "openrouter":
        return config.default_model
    else:
        return "gpt-4-turbo-preview"


# Global client instance
_llm_client: Optional[AsyncOpenAI] = None
_config: Optional[OpenRouterConfig] = None


def get_llm_client() -> AsyncOpenAI:
    """
    Get or create the global LLM client instance.

    Returns:
        AsyncOpenAI client
    """
    global _llm_client, _config

    if _llm_client is None:
        _config = OpenRouterConfig()
        _llm_client = create_llm_client(_config)

    return _llm_client


def get_llm_config() -> OpenRouterConfig:
    """
    Get the global LLM configuration.

    Returns:
        OpenRouterConfig instance
    """
    global _config

    if _config is None:
        _config = OpenRouterConfig()

    return _config
