"""LLM provider factory - instantiates the correct provider based on config."""

from app.core.config import settings
from app.llm.base import BaseLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Create and return the LLM provider based on LLM_PROVIDER env var.

    Supported providers:
    - "gemini": Google Gemini (default)
    - Add more providers here as needed (e.g., "openai", "anthropic")

    Returns:
        An instance of BaseLLMProvider.

    Raises:
        ValueError: If the configured provider is not supported.
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "gemini":
        from app.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider_name}'. "
            f"Supported providers: gemini. "
            f"Set LLM_PROVIDER env variable to a supported provider."
        )


# Singleton instance (lazy-loaded)
_provider_instance: BaseLLMProvider | None = None


def get_provider() -> BaseLLMProvider:
    """Get the singleton LLM provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_llm_provider()
    return _provider_instance


def reset_provider() -> None:
    """Reset the provider instance (useful for testing)."""
    global _provider_instance
    _provider_instance = None
