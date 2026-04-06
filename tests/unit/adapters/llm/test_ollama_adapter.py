"""
Unit tests for Ollama Adapter.

Tests the OllamaAdapter implementation with mocked API calls.
"""
import pytest
from unittest.mock import Mock, patch

from src.ports.llm_adapter import LLMConfig
from src.adapters.llm.ollama_adapter import OllamaAdapter
from src.domain.models import CharacterProfile, ValidationResult


@pytest.fixture
def ollama_config():
    """Fixture for Ollama LLM configuration."""
    return LLMConfig(
        provider="ollama",
        model_name="qwen2.5:72b",
        base_url="http://localhost:11434",
        temperature=0.3,
        max_tokens=2000
    )


@pytest.fixture
def simple_profile():
    """Fixture for a simple character profile."""
    return CharacterProfile(
        name="Test Character",
        basic_traits=["practical", "direct"]
    )


@pytest.fixture
def mock_ollama_response():
    """Fixture for mocked Ollama API response."""
    return {
        "response": """```json
{
  "is_valid": true,
  "confidence_score": 0.92,
  "severity": "passed",
  "summary": "The excerpt matches the character's voice well.",
  "flagged_passages": [],
  "suggestions": []
}
```"""
    }


class TestOllamaAdapter:
    """Tests for OllamaAdapter."""

    def test_initialization_with_base_url(self, ollama_config):
        """Test initialization with explicit base URL."""
        adapter = OllamaAdapter(ollama_config)

        assert adapter.config == ollama_config
        assert adapter.base_url == "http://localhost:11434"
        assert adapter.api_endpoint == "http://localhost:11434/api/generate"

    def test_initialization_default_base_url(self):
        """Test initialization with default base URL."""
        config = LLMConfig(
            provider="ollama",
            model_name="qwen2.5:72b"
        )

        adapter = OllamaAdapter(config)

        assert adapter.base_url == "http://localhost:11434"

    def test_get_model_name(self, ollama_config):
        """Test getting model name."""
        adapter = OllamaAdapter(ollama_config)

        assert adapter.get_model_name() == "qwen2.5:72b"

    def test_get_provider(self, ollama_config):
        """Test getting provider name."""
        adapter = OllamaAdapter(ollama_config)

        assert adapter.get_provider() == "ollama"

    @patch('src.adapters.llm.ollama_adapter.requests.post')
    def test_validate_voice_success(
        self,
        mock_post,
        ollama_config,
        simple_profile,
        mock_ollama_response
    ):
        """Test successful voice validation."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        adapter = OllamaAdapter(ollama_config)
        result = adapter.validate_voice(
            profile=simple_profile,
            excerpt="That's the way it is."
        )

        # Verify result
        assert isinstance(result, ValidationResult)
        assert result.character_name == "Test Character"
        assert result.is_valid is True
        assert result.confidence_score == 0.92
        assert result.severity == "passed"
        assert result.model_used == "qwen2.5:72b"
        assert result.processing_time_ms >= 0  # Can be 0 in mocked tests

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "http://localhost:11434/api/generate" in call_args.args
        payload = call_args.kwargs["json"]
        assert payload["model"] == "qwen2.5:72b"
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.3

    @patch('src.adapters.llm.ollama_adapter.requests.post')
    def test_validate_voice_empty_excerpt(
        self,
        mock_post,
        ollama_config,
        simple_profile
    ):
        """Test validation with empty excerpt raises ValueError."""
        adapter = OllamaAdapter(ollama_config)

        with pytest.raises(ValueError, match="Excerpt cannot be empty"):
            adapter.validate_voice(profile=simple_profile, excerpt="")

    @patch('src.adapters.llm.ollama_adapter.requests.post')
    def test_validate_voice_timeout(
        self,
        mock_post,
        ollama_config,
        simple_profile
    ):
        """Test validation handles timeout."""
        import requests
        mock_post.side_effect = requests.Timeout("Timeout")

        adapter = OllamaAdapter(ollama_config)

        with pytest.raises(TimeoutError, match="Ollama API timeout"):
            adapter.validate_voice(profile=simple_profile, excerpt="Test")

    @patch('src.adapters.llm.ollama_adapter.requests.post')
    def test_validate_voice_connection_error(
        self,
        mock_post,
        ollama_config,
        simple_profile
    ):
        """Test validation handles connection errors."""
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        adapter = OllamaAdapter(ollama_config)

        with pytest.raises(RuntimeError, match="Cannot connect to Ollama"):
            adapter.validate_voice(profile=simple_profile, excerpt="Test")

    @patch('src.adapters.llm.ollama_adapter.requests.post')
    def test_validate_voice_http_error(
        self,
        mock_post,
        ollama_config,
        simple_profile
    ):
        """Test validation handles HTTP errors."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Error")
        mock_post.return_value = mock_response

        adapter = OllamaAdapter(ollama_config)

        with pytest.raises(RuntimeError, match="Ollama API HTTP error"):
            adapter.validate_voice(profile=simple_profile, excerpt="Test")

    @patch('src.adapters.llm.ollama_adapter.requests.get')
    def test_health_check_success(self, mock_get, ollama_config):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:72b"},
                {"name": "llama3.1:70b"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        adapter = OllamaAdapter(ollama_config)
        result = adapter.health_check()

        assert result is True
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags",
            timeout=5
        )

    @patch('src.adapters.llm.ollama_adapter.requests.get')
    def test_health_check_model_not_available(self, mock_get, ollama_config):
        """Test health check when model is not available."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.1:70b"}  # Different model
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        adapter = OllamaAdapter(ollama_config)
        result = adapter.health_check()

        assert result is False

    @patch('src.adapters.llm.ollama_adapter.requests.get')
    def test_health_check_connection_failure(self, mock_get, ollama_config):
        """Test health check when Ollama is not running."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Cannot connect")

        adapter = OllamaAdapter(ollama_config)
        result = adapter.health_check()

        assert result is False

    def test_parse_validation_response_json_in_markdown(self, ollama_config):
        """Test parsing JSON wrapped in markdown code blocks."""
        adapter = OllamaAdapter(ollama_config)

        response_text = """```json
{
  "is_valid": true,
  "confidence_score": 0.95,
  "severity": "passed"
}
```"""

        result = adapter._parse_validation_response(response_text)

        assert result["is_valid"] is True
        assert result["confidence_score"] == 0.95

    def test_parse_validation_response_with_extra_text(self, ollama_config):
        """Test parsing JSON with extra text before/after."""
        adapter = OllamaAdapter(ollama_config)

        response_text = """Here's my analysis:

{
  "is_valid": false,
  "confidence_score": 0.70
}

Hope this helps!"""

        result = adapter._parse_validation_response(response_text)

        assert result["is_valid"] is False
        assert result["confidence_score"] == 0.70

    def test_parse_validation_response_invalid_json(self, ollama_config):
        """Test parsing invalid JSON raises ValueError."""
        adapter = OllamaAdapter(ollama_config)

        response_text = "This is not valid JSON at all"

        with pytest.raises(ValueError, match="Failed to parse Ollama response"):
            adapter._parse_validation_response(response_text)

    def test_build_validation_prompt(self, ollama_config, simple_profile):
        """Test building validation prompt."""
        adapter = OllamaAdapter(ollama_config)

        prompt = adapter._build_validation_prompt(
            profile=simple_profile,
            excerpt="Test excerpt"
        )

        assert "Test Character" in prompt
        assert "practical" in prompt
        assert "direct" in prompt
        assert "Test excerpt" in prompt
        assert "IMPORTANT: Respond ONLY with the JSON object" in prompt
