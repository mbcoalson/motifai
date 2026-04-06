"""
Unit tests for Claude Adapter.

Tests the ClaudeAdapter implementation with mocked API calls.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ports.llm_adapter import LLMConfig
from src.adapters.llm.claude_adapter import ClaudeAdapter
from src.domain.models import CharacterProfile, ValidationResult, FlaggedPassage


@pytest.fixture
def claude_config():
    """Fixture for Claude LLM configuration."""
    return LLMConfig(
        provider="claude",
        model_name="claude-sonnet-4-5-20250929",
        api_key="test-api-key-123",
        temperature=0.3,
        max_tokens=2000
    )


@pytest.fixture
def simple_profile():
    """Fixture for a simple character profile."""
    return CharacterProfile(
        name="Test Character",
        basic_traits=["practical", "direct"],
        forbidden_vocabulary=["indubitably", "perchance"]
    )


@pytest.fixture
def mock_claude_response():
    """Fixture for mocked Claude API response."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = """```json
{
  "is_valid": false,
  "confidence_score": 0.85,
  "severity": "moderate",
  "summary": "The excerpt contains vocabulary inconsistent with the character.",
  "flagged_passages": [
    {
      "text": "indubitably",
      "reason": "This word is in the character's forbidden vocabulary list",
      "severity": "critical",
      "suggestion": "Use simpler language like 'definitely' or 'for sure'"
    }
  ],
  "suggestions": [
    "Simplify vocabulary to match character's practical nature"
  ]
}
```"""
    return mock_response


class TestClaudeAdapter:
    """Tests for ClaudeAdapter."""

    def test_initialization_success(self, claude_config):
        """Test successful initialization with API key."""
        adapter = ClaudeAdapter(claude_config)

        assert adapter.config == claude_config
        assert adapter.client is not None

    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        config = LLMConfig(
            provider="claude",
            model_name="claude-sonnet-4-5-20250929"
        )

        with pytest.raises(ValueError, match="Claude adapter requires an API key"):
            ClaudeAdapter(config)

    def test_get_model_name(self, claude_config):
        """Test getting model name."""
        adapter = ClaudeAdapter(claude_config)

        assert adapter.get_model_name() == "claude-sonnet-4-5-20250929"

    def test_get_provider(self, claude_config):
        """Test getting provider name."""
        adapter = ClaudeAdapter(claude_config)

        assert adapter.get_provider() == "claude"

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_validate_voice_success(
        self,
        mock_anthropic_class,
        claude_config,
        simple_profile,
        mock_claude_response
    ):
        """Test successful voice validation."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)
        result = adapter.validate_voice(
            profile=simple_profile,
            excerpt="Well, indubitably that's correct."
        )

        # Verify result
        assert isinstance(result, ValidationResult)
        assert result.character_name == "Test Character"
        assert result.is_valid is False
        assert result.confidence_score == 0.85
        assert result.severity == "moderate"
        assert result.model_used == "claude-sonnet-4-5-20250929"
        assert result.processing_time_ms >= 0  # Can be 0 in mocked tests

        # Verify flagged passages
        assert len(result.flagged_passages) == 1
        assert result.flagged_passages[0].text == "indubitably"
        assert result.flagged_passages[0].severity == "critical"

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-5-20250929"
        assert call_args.kwargs["temperature"] == 0.3
        assert call_args.kwargs["max_tokens"] == 2000

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_validate_voice_empty_excerpt(
        self,
        mock_anthropic_class,
        claude_config,
        simple_profile
    ):
        """Test validation with empty excerpt raises ValueError."""
        adapter = ClaudeAdapter(claude_config)

        with pytest.raises(ValueError, match="Excerpt cannot be empty"):
            adapter.validate_voice(profile=simple_profile, excerpt="")

        with pytest.raises(ValueError, match="Excerpt cannot be empty"):
            adapter.validate_voice(profile=simple_profile, excerpt="   ")

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_validate_voice_with_chapter(
        self,
        mock_anthropic_class,
        claude_config
    ):
        """Test validation with chapter number for arc stage detection."""
        from src.domain.models import ArcStage

        # Create profile with arc stages
        profile = CharacterProfile(
            name="Test Character",
            arc_stages=[
                ArcStage(
                    stage_id="stage_1",
                    name="Early Arc",
                    chapter_range={"start": 1, "end": 5},
                    vocabulary_register="Simple, practical language"
                )
            ]
        )

        # Create a fresh mock response for this test
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """```json
{
  "is_valid": true,
  "confidence_score": 0.90,
  "severity": "passed"
}
```"""

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)
        result = adapter.validate_voice(
            profile=profile,
            excerpt="Test excerpt",
            chapter=3
        )

        assert result.arc_stage_used == "stage_1"

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_validate_voice_api_timeout(
        self,
        mock_anthropic_class,
        claude_config,
        simple_profile
    ):
        """Test validation handles API timeout."""
        from anthropic import APITimeoutError

        mock_client = Mock()
        mock_client.messages.create.side_effect = APITimeoutError("Timeout")
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)

        with pytest.raises(TimeoutError, match="Claude API timeout"):
            adapter.validate_voice(profile=simple_profile, excerpt="Test")

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_validate_voice_api_error(
        self,
        mock_anthropic_class,
        claude_config,
        simple_profile
    ):
        """Test validation handles API errors."""
        mock_client = Mock()
        # Use a generic exception that will be caught
        mock_client.messages.create.side_effect = Exception("Connection Error")
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)

        with pytest.raises(RuntimeError, match="Unexpected error during validation"):
            adapter.validate_voice(profile=simple_profile, excerpt="Test")

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_health_check_success(self, mock_anthropic_class, claude_config):
        """Test successful health check."""
        mock_client = Mock()
        mock_response = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)
        result = adapter.health_check()

        assert result is True

    @patch('src.adapters.llm.claude_adapter.Anthropic')
    def test_health_check_failure(self, mock_anthropic_class, claude_config):
        """Test health check when API is unavailable."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Connection failed")
        mock_anthropic_class.return_value = mock_client

        adapter = ClaudeAdapter(claude_config)
        result = adapter.health_check()

        assert result is False

    def test_parse_validation_response_json_in_markdown(self, claude_config):
        """Test parsing JSON wrapped in markdown code blocks."""
        adapter = ClaudeAdapter(claude_config)

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
        assert result["severity"] == "passed"

    def test_parse_validation_response_plain_json(self, claude_config):
        """Test parsing plain JSON without markdown."""
        adapter = ClaudeAdapter(claude_config)

        response_text = """{
  "is_valid": false,
  "confidence_score": 0.75
}"""

        result = adapter._parse_validation_response(response_text)

        assert result["is_valid"] is False
        assert result["confidence_score"] == 0.75

    def test_parse_validation_response_invalid_json(self, claude_config):
        """Test parsing invalid JSON raises ValueError."""
        adapter = ClaudeAdapter(claude_config)

        response_text = "This is not valid JSON"

        with pytest.raises(ValueError, match="Failed to parse Claude response"):
            adapter._parse_validation_response(response_text)

    def test_parse_validation_response_missing_fields(self, claude_config):
        """Test parsing response with missing required fields."""
        adapter = ClaudeAdapter(claude_config)

        response_text = '{"is_valid": true}'  # Missing confidence_score

        with pytest.raises(ValueError, match="Response missing required fields"):
            adapter._parse_validation_response(response_text)

    def test_build_validation_prompt_minimal(self, claude_config, simple_profile):
        """Test building prompt with minimal profile."""
        adapter = ClaudeAdapter(claude_config)

        prompt = adapter._build_validation_prompt(
            profile=simple_profile,
            excerpt="Test excerpt"
        )

        assert "Test Character" in prompt
        assert "practical" in prompt
        assert "direct" in prompt
        assert "indubitably" in prompt  # Forbidden word
        assert "Test excerpt" in prompt

    def test_build_validation_prompt_with_context(self, claude_config, simple_profile):
        """Test building prompt with scene context."""
        adapter = ClaudeAdapter(claude_config)

        prompt = adapter._build_validation_prompt(
            profile=simple_profile,
            excerpt="Test excerpt",
            context="Character is angry and confrontational"
        )

        assert "Scene Context:" in prompt
        assert "angry and confrontational" in prompt
