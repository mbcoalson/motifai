"""
LLM Factory - Factory pattern for creating LLM adapters.

This module provides factory functions for creating LLM adapters
with minimal configuration, supporting easy switching between providers.
"""
import os
from typing import Optional

from src.ports.llm_adapter import LLMAdapter, LLMConfig
from .claude_adapter import ClaudeAdapter
from .ollama_adapter import OllamaAdapter


# Predefined model configurations
PREDEFINED_MODELS = {
    # Claude models (Tier 2 & 3)
    "claude-sonnet-4.5": {
        "provider": "claude",
        "model_name": "claude-sonnet-4-5-20250929",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "claude-opus-4.5": {
        "provider": "claude",
        "model_name": "claude-opus-4-5-20251101",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "claude-haiku-3.5": {
        "provider": "claude",
        "model_name": "claude-3-5-haiku-20241022",
        "temperature": 0.3,
        "max_tokens": 2000,
    },

    # Ollama models (Tier 1 - Free/Local)
    "qwen2.5-72b": {
        "provider": "ollama",
        "model_name": "qwen2.5:72b",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "llama3.1-70b": {
        "provider": "ollama",
        "model_name": "llama3.1:70b",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
    "mistral-large": {
        "provider": "ollama",
        "model_name": "mistral-large:latest",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
}


def create_llm_adapter(
    model_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout_seconds: int = 60,
    **kwargs
) -> LLMAdapter:
    """
    Create an LLM adapter for the specified model.

    This factory function automatically selects the appropriate adapter
    (Claude, Ollama, etc.) based on the model name and creates it with
    the provided configuration.

    Args:
        model_name: Name of the model (e.g., 'claude-sonnet-4.5', 'qwen2.5-72b')
                   Can be a predefined name or a custom model identifier
        api_key: API key for cloud providers (optional, auto-detected from env)
        base_url: Base URL for API (optional, defaults per provider)
        temperature: Sampling temperature (optional, uses model default)
        max_tokens: Maximum tokens in response (optional, uses model default)
        timeout_seconds: Request timeout in seconds (default: 60)
        **kwargs: Additional provider-specific configuration

    Returns:
        LLMAdapter instance configured for the specified model

    Raises:
        ValueError: If model_name is not recognized or configuration is invalid
        RuntimeError: If required dependencies are missing

    Examples:
        >>> # Use predefined model (auto-detects provider)
        >>> adapter = create_llm_adapter("claude-sonnet-4.5")
        >>>
        >>> # Use local Ollama model
        >>> adapter = create_llm_adapter("qwen2.5-72b")
        >>>
        >>> # Custom configuration
        >>> adapter = create_llm_adapter(
        ...     "claude-opus-4.5",
        ...     temperature=0.5,
        ...     max_tokens=3000
        ... )
    """
    # Check if this is a predefined model
    if model_name in PREDEFINED_MODELS:
        model_config = PREDEFINED_MODELS[model_name].copy()
        provider = model_config["provider"]

        # Override with provided values
        if temperature is not None:
            model_config["temperature"] = temperature
        if max_tokens is not None:
            model_config["max_tokens"] = max_tokens

    else:
        # Not predefined - try to infer provider from model name
        provider = _infer_provider_from_model_name(model_name)
        model_config = {
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature or 0.3,
            "max_tokens": max_tokens or 2000,
        }

    # Add common config
    model_config["timeout_seconds"] = timeout_seconds

    # Handle API key
    if api_key:
        model_config["api_key"] = api_key
    elif provider == "claude":
        # Auto-detect from environment
        model_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        if not model_config["api_key"]:
            raise ValueError(
                "Claude requires an API key. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

    # Handle base URL
    if base_url:
        model_config["base_url"] = base_url

    # Add any additional kwargs
    model_config.update(kwargs)

    # Create LLMConfig
    config = LLMConfig(**model_config)

    # Return appropriate adapter
    if provider == "claude":
        return ClaudeAdapter(config)
    elif provider == "ollama":
        return OllamaAdapter(config)
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: claude, ollama"
        )


def create_claude_adapter(
    model: str = "claude-sonnet-4-5-20250929",
    api_key: Optional[str] = None,
    **kwargs
) -> ClaudeAdapter:
    """
    Convenience function to create a Claude adapter.

    Args:
        model: Claude model name (default: Sonnet 4.5)
        api_key: Anthropic API key (optional, auto-detected from env)
        **kwargs: Additional configuration options

    Returns:
        ClaudeAdapter instance

    Example:
        >>> adapter = create_claude_adapter()
        >>> adapter = create_claude_adapter(model="claude-opus-4-5-20251101")
    """
    return create_llm_adapter(
        model_name=model,
        api_key=api_key,
        **kwargs
    )


def create_ollama_adapter(
    model: str = "qwen2.5:72b",
    base_url: Optional[str] = None,
    **kwargs
) -> OllamaAdapter:
    """
    Convenience function to create an Ollama adapter.

    Args:
        model: Ollama model name (default: Qwen 2.5 72B)
        base_url: Ollama API URL (optional, defaults to http://localhost:11434)
        **kwargs: Additional configuration options

    Returns:
        OllamaAdapter instance

    Example:
        >>> adapter = create_ollama_adapter()
        >>> adapter = create_ollama_adapter(model="llama3.1:70b")
    """
    return create_llm_adapter(
        model_name=model,
        base_url=base_url,
        **kwargs
    )


def _infer_provider_from_model_name(model_name: str) -> str:
    """
    Infer the provider from a model name.

    Args:
        model_name: Model name to analyze

    Returns:
        Provider name ('claude', 'ollama', etc.)

    Raises:
        ValueError: If provider cannot be inferred
    """
    model_lower = model_name.lower()

    if any(keyword in model_lower for keyword in ["claude", "sonnet", "opus", "haiku"]):
        return "claude"
    elif any(keyword in model_lower for keyword in ["qwen", "llama", "mistral", "phi"]):
        return "ollama"
    else:
        raise ValueError(
            f"Cannot infer provider from model name: {model_name}. "
            f"Please use a predefined model name or specify provider explicitly."
        )


def list_predefined_models() -> dict[str, dict]:
    """
    Get all predefined model configurations.

    Returns:
        Dict mapping model names to their configurations

    Example:
        >>> models = list_predefined_models()
        >>> for name, config in models.items():
        ...     print(f"{name}: {config['provider']}")
    """
    return PREDEFINED_MODELS.copy()


def get_model_info(model_name: str) -> dict:
    """
    Get information about a specific model.

    Args:
        model_name: Name of the predefined model

    Returns:
        Dict with model configuration

    Raises:
        ValueError: If model_name is not predefined

    Example:
        >>> info = get_model_info("claude-sonnet-4.5")
        >>> print(info["provider"])
        claude
    """
    if model_name not in PREDEFINED_MODELS:
        raise ValueError(
            f"Unknown model: {model_name}. "
            f"Available models: {', '.join(PREDEFINED_MODELS.keys())}"
        )
    return PREDEFINED_MODELS[model_name].copy()
