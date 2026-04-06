"""
LLM Adapter Port - Abstract interface for LLM providers.

This port defines the contract that all LLM adapters must implement,
enabling the system to swap between different LLM providers (Claude, Ollama, etc.)
without changing the core domain logic.
"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import CharacterProfile, ValidationResult


class LLMConfig(BaseModel):
    """
    Configuration for LLM adapter.

    This model allows for flexible configuration of different LLM providers
    while maintaining type safety.
    """
    provider: str = Field(
        ...,
        description="LLM provider name (e.g., 'claude', 'ollama', 'openai')"
    )
    model_name: str = Field(
        ...,
        description="Specific model to use (e.g., 'claude-sonnet-4.5', 'qwen2.5-72b')"
    )
    api_key: Optional[str] = Field(
        None,
        description="API key for cloud providers (not needed for local models)"
    )
    base_url: Optional[str] = Field(
        None,
        description="Base URL for API (e.g., Ollama endpoint, custom proxy)"
    )
    temperature: float = Field(
        0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, higher = more creative)"
    )
    max_tokens: int = Field(
        2000,
        ge=1,
        le=100000,
        description="Maximum tokens in response"
    )
    timeout_seconds: int = Field(
        60,
        ge=1,
        le=600,
        description="Request timeout in seconds"
    )
    stream: bool = Field(
        False,
        description="Whether to stream responses (if supported)"
    )

    model_config = ConfigDict(extra="allow")  # Allow provider-specific options


class LLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.

    All LLM provider implementations must inherit from this class and
    implement the validate_voice method. This ensures consistent behavior
    across different LLM backends.

    The adapter is responsible for:
    1. Constructing appropriate prompts from character profiles and excerpts
    2. Calling the LLM provider's API
    3. Parsing the response into a ValidationResult
    4. Handling errors gracefully
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM adapter with configuration.

        Args:
            config: LLMConfig object with provider-specific settings
        """
        self.config = config

    @abstractmethod
    def validate_voice(
        self,
        profile: CharacterProfile,
        excerpt: str,
        chapter: Optional[int] = None,
        context: Optional[str] = None,
        pre_context: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate a text excerpt against a character's voice profile.

        This is the primary interface method that all adapters must implement.

        Args:
            profile: CharacterProfile containing the character's voice characteristics
            excerpt: The text to validate (dialogue or narrative)
            chapter: Optional chapter number to select appropriate arc stage
            context: Optional scene context passed to the LLM prompt
            pre_context: Optional pre-computed deterministic findings to inject before
                the excerpt, instructing the LLM not to re-flag already-caught violations

        Returns:
            ValidationResult with validation status, confidence, and flagged issues

        Raises:
            ValueError: If profile or excerpt is invalid
            RuntimeError: If LLM call fails
            TimeoutError: If LLM call exceeds timeout
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the LLM provider is available and responding.

        This method should perform a lightweight check to verify the
        LLM service is accessible (e.g., ping endpoint, test API key).

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    def get_model_name(self) -> str:
        """
        Get the model name for this adapter.

        Returns:
            String identifying the model (e.g., 'claude-sonnet-4.5')
        """
        return self.config.model_name

    def get_provider(self) -> str:
        """
        Get the provider name for this adapter.

        Returns:
            String identifying the provider (e.g., 'claude', 'ollama')
        """
        return self.config.provider
