"""Unit tests for ValidationService orchestrator."""
import pytest
from unittest.mock import Mock
from datetime import datetime

from src.domain.services.validation_service import ValidationService
from src.domain.models import (
    CharacterProfile,
    ArcStage,
    ValidationResult,
    FlaggedPassage,
)


@pytest.fixture
def basic_profile():
    """Fixture for a basic character profile."""
    return CharacterProfile(
        name="Santiago Esposito",
        basic_traits=["practical", "blue-collar"],
        forbidden_vocabulary=["algorithm", "indubitably"],
        signature_phrases=["Water does what water does"],
    )


@pytest.fixture
def profile_with_arc_stages():
    """Fixture for a profile with arc stages."""
    stage1 = ArcStage(
        stage_id="stage_1",
        name="Pre-transformation skeptic",
        chapter_range={"start": 1, "end": 5},
    )
    return CharacterProfile(
        name="Santiago Esposito",
        arc_stages=[stage1],
        forbidden_vocabulary=["algorithm"],
    )


@pytest.fixture
def mock_llm_adapter():
    """Fixture for mocked LLM adapter."""
    return Mock()


class TestValidationService:
    """Tests for ValidationService.validate() method."""

    def test_validate_merges_deterministic_and_llm_flags(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that deterministic and LLM flags are both present in result."""
        # Setup: deterministic will find "algorithm", LLM will find something else
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The algorithm processes water.",
            is_valid=False,
            confidence_score=0.85,
            severity="moderate",
            flagged_passages=[
                FlaggedPassage(
                    text="processes",
                    reason="Too technical",
                    severity="moderate",
                )
            ],
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "The algorithm processes water.")

        # Both deterministic "algorithm" and LLM "processes" should be present
        assert len(result.flagged_passages) == 2
        flagged_texts = {f.text for f in result.flagged_passages}
        assert "algorithm" in flagged_texts
        assert "processes" in flagged_texts

    def test_validate_deduplicates_same_word(self, basic_profile, mock_llm_adapter):
        """Test that duplicate flags from LLM and deterministic use LLM's entry."""
        # Setup: both deterministic and LLM flag "algorithm"
        llm_flag = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon inconsistent with character voice",
            severity="critical",
            suggestion="Use plain language like 'process' or 'pattern'",
        )
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The algorithm processes water.",
            is_valid=False,
            confidence_score=0.9,
            severity="critical",
            flagged_passages=[llm_flag],
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "The algorithm processes water.")

        # Only ONE "algorithm" entry (LLM's, which has richer suggestion)
        algorithm_flags = [f for f in result.flagged_passages if f.text == "algorithm"]
        assert len(algorithm_flags) == 1
        assert algorithm_flags[0].suggestion is not None
        assert "Use plain language" in algorithm_flags[0].suggestion

    def test_validate_deterministic_only_flags_present_when_llm_finds_nothing(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that deterministic flags appear when LLM finds no issues."""
        # LLM returns no flagged passages
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The algorithm processes water.",
            is_valid=True,
            confidence_score=0.8,
            severity="passed",
            flagged_passages=None,
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "The algorithm processes water.")

        # Deterministic "algorithm" flag should be in result
        assert len(result.flagged_passages) >= 1
        assert any(f.text == "algorithm" for f in result.flagged_passages)

    def test_validate_enriched_context_contains_scene_context(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that scene_context is passed to the LLM adapter."""
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.9,
            severity="passed",
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        scene_context = "Storm approaching, tension rising"
        service.validate(
            basic_profile,
            "Test excerpt",
            scene_context=scene_context,
        )

        # Verify that adapter was called
        mock_llm_adapter.validate_voice.assert_called_once()
        call_args = mock_llm_adapter.validate_voice.call_args
        context_arg = call_args.kwargs["context"]

        # Scene context should be in the enriched context
        assert scene_context in context_arg

    def test_validate_enriched_context_contains_deterministic_injection(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that deterministic result is injected into context."""
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.9,
            severity="passed",
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        service.validate(basic_profile, "Test excerpt")

        # Verify adapter was called with enriched context
        mock_llm_adapter.validate_voice.assert_called_once()
        call_args = mock_llm_adapter.validate_voice.call_args
        pre_context_arg = call_args.kwargs["pre_context"]

        # Deterministic injection content should be present in pre_context
        assert "Pre-Computed Rule Violations" in pre_context_arg
        assert "Arc Stage" in pre_context_arg

    def test_validate_is_valid_false_when_critical_deterministic_flag(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that critical deterministic flag overrides LLM's is_valid=True."""
        # LLM says is_valid=True, but deterministic finds critical "algorithm" flag
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The algorithm processes water.",
            is_valid=True,
            confidence_score=0.8,
            severity="passed",
            flagged_passages=None,
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "The algorithm processes water.")

        # Deterministic critical flag should force is_valid=False
        assert result.is_valid is False

    def test_validate_passes_chapter_to_adapter(self, profile_with_arc_stages, mock_llm_adapter):
        """Test that chapter number is forwarded to the LLM adapter."""
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.9,
            severity="passed",
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        service.validate(
            profile_with_arc_stages,
            "Test excerpt",
            chapter=3,
        )

        # Verify adapter was called with chapter=3
        mock_llm_adapter.validate_voice.assert_called_once()
        call_args = mock_llm_adapter.validate_voice.call_args
        assert call_args.kwargs["chapter"] == 3

    def test_validate_returns_llm_scalar_fields(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that returned result preserves all LLM scalar fields."""
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.95,
            severity="passed",
            arc_stage_used="stage_1",
            model_used="claude-haiku-3.5",
            summary="All checks passed",
            suggestions=["Consider emphasizing sensory details"],
            processing_time_ms=150.5,
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "Test excerpt")

        # Verify scalar fields are preserved from LLM result
        assert result.character_name == "Santiago Esposito"
        assert result.excerpt == "Test excerpt"
        assert result.confidence_score == 0.95
        assert result.severity == "passed"
        assert result.arc_stage_used == "stage_1"
        assert result.model_used == "claude-haiku-3.5"
        assert result.summary == "All checks passed"
        assert result.suggestions == ["Consider emphasizing sensory details"]
        assert result.processing_time_ms == 150.5

    def test_validate_deduplicates_case_insensitive(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that deduplication works case-insensitively."""
        # Deterministic finds "algorithm", LLM finds "Algorithm"
        llm_flag = FlaggedPassage(
            text="Algorithm",
            reason="Technical jargon",
            severity="critical",
            suggestion="Use simpler word",
        )
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The Algorithm processes water.",
            is_valid=False,
            confidence_score=0.9,
            severity="critical",
            flagged_passages=[llm_flag],
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "The Algorithm processes water.")

        # Should deduplicate despite case difference
        algorithm_flags = [
            f for f in result.flagged_passages if f.text.lower() == "algorithm"
        ]
        assert len(algorithm_flags) == 1

    def test_validate_with_no_llm_flags_empty_result(
        self, basic_profile, mock_llm_adapter
    ):
        """Test behavior when LLM returns empty flagged_passages list."""
        # LLM explicitly returns empty list (not None)
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.8,
            severity="passed",
            flagged_passages=[],  # Empty list
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(basic_profile, "Test excerpt")

        # No deterministic hits (excerpt doesn't contain forbidden words) + LLM returned empty
        # list → merged is empty → service returns None rather than an empty list
        assert result.flagged_passages is None

    def test_validate_scene_context_passed_as_context_deterministic_as_pre_context(
        self, basic_profile, mock_llm_adapter
    ):
        """Test that scene_context and deterministic injection reach the adapter separately.

        scene_context goes to the 'context' parameter (scene context slot in the prompt).
        Deterministic findings go to the 'pre_context' parameter (rule violations header).
        This ensures the LLM receives the 'Do not re-flag' instruction for deterministic items.
        """
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Test excerpt",
            is_valid=True,
            confidence_score=0.9,
            severity="passed",
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        scene_context = "Storm approaching"
        service.validate(
            basic_profile,
            "Test excerpt",
            scene_context=scene_context,
        )

        call_args = mock_llm_adapter.validate_voice.call_args
        # scene_context flows through cleanly as 'context'
        assert call_args.kwargs["context"] == scene_context
        # Deterministic injection arrives in 'pre_context', not mixed into context
        assert call_args.kwargs["pre_context"] is not None
        assert "Pre-Computed Rule Violations" in call_args.kwargs["pre_context"]

    def test_validate_multiple_deterministic_flags_merged_with_llm(
        self, basic_profile, mock_llm_adapter
    ):
        """Test merging multiple deterministic flags with LLM flags."""
        # Profile will find both "algorithm" and "indubitably" as deterministic violations
        llm_flag = FlaggedPassage(
            text="something_else",
            reason="Other issue",
            severity="moderate",
        )
        mock_llm_adapter.validate_voice.return_value = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="The algorithm is indubitably complex.",
            is_valid=False,
            confidence_score=0.85,
            severity="moderate",
            flagged_passages=[llm_flag],
            model_used="claude-haiku-3.5",
        )

        service = ValidationService(mock_llm_adapter)
        result = service.validate(
            basic_profile,
            "The algorithm is indubitably complex.",
        )

        # Should have at least the LLM flag + multiple deterministic flags
        assert len(result.flagged_passages) >= 2
