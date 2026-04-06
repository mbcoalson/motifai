"""
Unit tests for LLM Factory.

Tests the factory functions for creating LLM adapters with various
configurations and providers.
"""
import pytest
import os

from src.ports.llm_adapter import LLMConfig
from src.adapters.llm import (
    create_llm_adapter,
    create_claude_adapter,
    create_ollama_adapter,
    list_predefined_models,
    get_model_info,
)
from src.adapters.llm.claude_adapter import ClaudeAdapter
from src.adapters.llm.ollama_adapter import OllamaAdapter


class TestLLMFactory:
    """Tests for LLM factory functions."""

    def test_list_predefined_models(self):
        """Test listing all predefined models."""
        models = list_predefined_models()

        assert isinstance(models, dict)
        assert len(models) > 0

        # Check for expected models
        assert "claude-sonnet-4.5" in models
        assert "qwen2.5-72b" in models

        # Verify structure
        for name, config in models.items():
            assert "provider" in config
            assert "model_name" in config
            assert "temperature" in config
            assert "max_tokens" in config

    def test_get_model_info_success(self):
        """Test getting info for a valid predefined model."""
        info = get_model_info("claude-sonnet-4.5")

        assert info["provider"] == "claude"
        assert "model_name" in info
        assert info["temperature"] == 0.3
        assert info["max_tokens"] == 2000

    def test_get_model_info_unknown_model(self):
        """Test getting info for an unknown model raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_model_info("nonexistent-model")

    def test_create_claude_adapter_with_api_key(self):
        """Test creating Claude adapter with explicit API key."""
        adapter = create_claude_adapter(api_key="test-key-123")

        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.config.provider == "claude"
        assert adapter.config.api_key == "test-key-123"

    def test_create_claude_adapter_from_env(self, monkeypatch):
        """Test creating Claude adapter with API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-test-key")

        adapter = create_claude_adapter()

        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.config.api_key == "env-test-key"

    def test_create_claude_adapter_missing_key(self, monkeypatch):
        """Test creating Claude adapter without API key raises error."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="Claude requires an API key"):
            create_claude_adapter()

    def test_create_ollama_adapter_default(self):
        """Test creating Ollama adapter with defaults."""
        adapter = create_ollama_adapter()

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.config.provider == "ollama"
        assert adapter.config.model_name == "qwen2.5:72b"
        assert adapter.base_url == "http://localhost:11434"

    def test_create_ollama_adapter_custom_model(self):
        """Test creating Ollama adapter with custom model."""
        adapter = create_ollama_adapter(model="llama3.1:70b")

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.config.model_name == "llama3.1:70b"

    def test_create_ollama_adapter_custom_url(self):
        """Test creating Ollama adapter with custom base URL."""
        adapter = create_ollama_adapter(base_url="http://remote-server:11434")

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.base_url == "http://remote-server:11434"

    def test_create_llm_adapter_predefined_claude(self, monkeypatch):
        """Test creating adapter from predefined Claude model."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        adapter = create_llm_adapter("claude-sonnet-4.5")

        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.get_provider() == "claude"

    def test_create_llm_adapter_predefined_ollama(self):
        """Test creating adapter from predefined Ollama model."""
        adapter = create_llm_adapter("qwen2.5-72b")

        assert isinstance(adapter, OllamaAdapter)
        assert adapter.get_provider() == "ollama"

    def test_create_llm_adapter_custom_temperature(self, monkeypatch):
        """Test creating adapter with custom temperature."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        adapter = create_llm_adapter("claude-sonnet-4.5", temperature=0.7)

        assert adapter.config.temperature == 0.7

    def test_create_llm_adapter_custom_max_tokens(self, monkeypatch):
        """Test creating adapter with custom max_tokens."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        adapter = create_llm_adapter("claude-sonnet-4.5", max_tokens=3000)

        assert adapter.config.max_tokens == 3000

    def test_create_llm_adapter_infer_claude_from_name(self, monkeypatch):
        """Test inferring Claude provider from model name."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        adapter = create_llm_adapter("claude-custom-model")

        assert isinstance(adapter, ClaudeAdapter)

    def test_create_llm_adapter_infer_ollama_from_name(self):
        """Test inferring Ollama provider from model name."""
        adapter = create_llm_adapter("qwen2.5:custom")

        assert isinstance(adapter, OllamaAdapter)

    def test_create_llm_adapter_unknown_provider(self):
        """Test creating adapter with unknown provider fails."""
        with pytest.raises(ValueError, match="Cannot infer provider"):
            create_llm_adapter("unknown-model-xyz")

    def test_adapter_get_model_name(self):
        """Test adapter's get_model_name method."""
        adapter = create_ollama_adapter(model="llama3.1:70b")

        assert adapter.get_model_name() == "llama3.1:70b"

    def test_adapter_get_provider(self):
        """Test adapter's get_provider method."""
        adapter = create_ollama_adapter()

        assert adapter.get_provider() == "ollama"


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_llm_config_minimal(self):
        """Test creating LLMConfig with minimal required fields."""
        config = LLMConfig(
            provider="claude",
            model_name="claude-sonnet-4-5-20250929"
        )

        assert config.provider == "claude"
        assert config.model_name == "claude-sonnet-4-5-20250929"
        assert config.temperature == 0.3  # Default
        assert config.max_tokens == 2000  # Default
        assert config.timeout_seconds == 60  # Default
        assert config.stream is False  # Default

    def test_llm_config_full(self):
        """Test creating LLMConfig with all fields."""
        config = LLMConfig(
            provider="claude",
            model_name="claude-opus-4-5-20251101",
            api_key="test-key",
            base_url="https://api.anthropic.com",
            temperature=0.5,
            max_tokens=4000,
            timeout_seconds=120,
            stream=True
        )

        assert config.provider == "claude"
        assert config.model_name == "claude-opus-4-5-20251101"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.anthropic.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 4000
        assert config.timeout_seconds == 120
        assert config.stream is True

    def test_llm_config_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperatures
        config = LLMConfig(provider="test", model_name="test", temperature=0.0)
        assert config.temperature == 0.0

        config = LLMConfig(provider="test", model_name="test", temperature=2.0)
        assert config.temperature == 2.0

        # Invalid temperatures
        with pytest.raises(Exception):  # Pydantic validation error
            LLMConfig(provider="test", model_name="test", temperature=-0.1)

        with pytest.raises(Exception):  # Pydantic validation error
            LLMConfig(provider="test", model_name="test", temperature=2.1)

    def test_llm_config_allows_extra_fields(self):
        """Test that LLMConfig allows extra provider-specific fields."""
        config = LLMConfig(
            provider="custom",
            model_name="custom-model",
            custom_field="custom_value",
            another_option=42
        )

        assert config.custom_field == "custom_value"
        assert config.another_option == 42
