"""Unit tests for DeterministicValidator and DeterministicResult."""
import pytest
from datetime import date

from src.domain.services.deterministic_validator import (
    DeterministicValidator,
    DeterministicResult,
)
from src.domain.models import (
    CharacterProfile,
    ArcStage,
    FlaggedPassage,
)


@pytest.fixture
def basic_profile():
    """Fixture for a basic character profile with forbidden vocabulary."""
    return CharacterProfile(
        name="Santiago Esposito",
        basic_traits=["practical", "blue-collar"],
        forbidden_vocabulary=["algorithm", "indubitably", "perchance"],
        signature_phrases=["Water does what water does", "Tide's pulling"],
    )


@pytest.fixture
def profile_with_arc_stages():
    """Fixture for a profile with arc stages."""
    stage1 = ArcStage(
        stage_id="stage_1",
        name="Pre-transformation skeptic",
        chapter_range={"start": 1, "end": 5},
    )
    stage2 = ArcStage(
        stage_id="stage_2",
        name="Transitional",
        chapter_range={"start": 6, "end": 10},
    )
    return CharacterProfile(
        name="Santiago Esposito",
        arc_stages=[stage1, stage2],
        forbidden_vocabulary=["algorithm"],
    )


@pytest.fixture
def validator():
    """Fixture for DeterministicValidator instance."""
    return DeterministicValidator()


class TestDeterministicValidator:
    """Tests for DeterministicValidator.validate() method."""

    def test_validate_forbidden_vocab_found(self, validator, basic_profile):
        """Test that forbidden vocabulary is detected and flagged with critical severity."""
        excerpt = "Santiago analyzed the algorithm carefully."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is True
        assert len(result.forbidden_vocab_flags) == 1
        assert result.forbidden_vocab_flags[0].text == "algorithm"
        assert result.forbidden_vocab_flags[0].severity == "critical"
        assert "forbidden vocabulary" in result.forbidden_vocab_flags[0].reason

    def test_validate_forbidden_vocab_not_found(self, validator, basic_profile):
        """Test that clean excerpt has no forbidden vocabulary flags."""
        excerpt = "Water does what water does."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is False
        assert len(result.forbidden_vocab_flags) == 0

    def test_validate_forbidden_vocab_whole_word_only(self, validator, basic_profile):
        """Test that partial word matches are ignored (whole-word matching)."""
        excerpt = "The algorithms used in nature are complex."
        result = validator.validate(basic_profile, excerpt)

        # "algorithms" should not match "algorithm" in the forbidden list
        assert result.has_violations is False
        assert len(result.forbidden_vocab_flags) == 0

    def test_validate_forbidden_vocab_case_insensitive(self, validator, basic_profile):
        """Test that forbidden vocabulary matching is case-insensitive."""
        excerpt = "Santiago used an ALGORITHM to solve it."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is True
        assert len(result.forbidden_vocab_flags) == 1
        assert result.forbidden_vocab_flags[0].text == "algorithm"

    def test_validate_arc_stage_detected(self, validator, profile_with_arc_stages):
        """Test that arc stage is correctly detected by chapter."""
        excerpt = "Some text content"
        result = validator.validate(profile_with_arc_stages, excerpt, chapter=3)

        assert result.arc_stage is not None
        assert result.arc_stage.stage_id == "stage_1"

    def test_validate_arc_stage_none_when_no_match(self, validator, profile_with_arc_stages):
        """Test that arc_stage is None when chapter doesn't match any range."""
        excerpt = "Some text content"
        result = validator.validate(profile_with_arc_stages, excerpt, chapter=99)

        assert result.arc_stage is None

    def test_validate_signature_phrases_found(self, validator, basic_profile):
        """Test that signature phrases are detected in the excerpt."""
        excerpt = "Water does what water does. That's how it works."
        result = validator.validate(basic_profile, excerpt)

        assert len(result.signature_phrases_found) > 0
        assert "Water does what water does" in result.signature_phrases_found

    def test_validate_signature_phrases_partial_match(self, validator, basic_profile):
        """Test that signature phrases are matched as partial matches (substring)."""
        excerpt = "Tide's pulling harder than usual."
        result = validator.validate(basic_profile, excerpt)

        assert len(result.signature_phrases_found) > 0
        assert "Tide's pulling" in result.signature_phrases_found

    def test_validate_no_forbidden_vocab_field(self, validator):
        """Test that validation doesn't crash when profile has no forbidden_vocabulary."""
        profile = CharacterProfile(name="Test Character")
        excerpt = "Some text with algorithm and other words"
        result = validator.validate(profile, excerpt)

        # Should not crash; forbidden_vocab_flags should be empty
        assert result.has_violations is False
        assert len(result.forbidden_vocab_flags) == 0

    def test_validate_has_violations_true(self, validator, basic_profile):
        """Test that has_violations is True when forbidden word is found."""
        excerpt = "Using the indubitably useful algorithm."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is True

    def test_validate_has_violations_false(self, validator, basic_profile):
        """Test that has_violations is False when no violations found."""
        excerpt = "A clean, simple text about the water."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is False

    def test_validate_multiple_forbidden_words(self, validator, basic_profile):
        """Test that multiple forbidden words are all flagged."""
        excerpt = "Algorithm and indubitably, he used both terms."
        result = validator.validate(basic_profile, excerpt)

        assert result.has_violations is True
        assert len(result.forbidden_vocab_flags) == 2
        flagged_texts = {flag.text for flag in result.forbidden_vocab_flags}
        assert "algorithm" in flagged_texts
        assert "indubitably" in flagged_texts

    def test_validate_with_chapter_and_date(self, validator):
        """Test that chapter takes precedence over story_date for arc stage."""
        stage1 = ArcStage(
            stage_id="stage_1",
            name="Early",
            chapter_range={"start": 1, "end": 5},
        )
        stage2 = ArcStage(
            stage_id="stage_2",
            name="Late",
            date_range={"start": date(2024, 1, 1), "end": date(2024, 3, 31)},
        )
        profile = CharacterProfile(
            name="Test",
            arc_stages=[stage1, stage2],
        )

        result = validator.validate(
            profile,
            "Test",
            chapter=3,
            story_date=date(2024, 5, 15),
        )

        # Chapter should take precedence
        assert result.arc_stage is not None
        assert result.arc_stage.stage_id == "stage_1"


class TestDeterministicResult:
    """Tests for DeterministicResult.to_context_injection() method."""

    def test_to_context_injection_with_violations(self):
        """Test context injection output when violations are present."""
        flag = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon not fitting character voice",
            severity="critical",
        )
        stage = ArcStage(
            stage_id="stage_1",
            name="Early Stage",
        )
        result = DeterministicResult(
            arc_stage=stage,
            forbidden_vocab_flags=[flag],
            signature_phrases_found=["Water does"],
            has_violations=True,
        )

        output = result.to_context_injection()

        assert "Pre-Computed Rule Violations" in output
        assert "algorithm" in output
        assert "stage_1" in output
        assert "Water does" in output
        assert "confidence: 1.0" in output

    def test_to_context_injection_no_violations(self):
        """Test context injection output when no violations are present."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early Stage",
        )
        result = DeterministicResult(
            arc_stage=stage,
            forbidden_vocab_flags=[],
            signature_phrases_found=[],
            has_violations=False,
        )

        output = result.to_context_injection()

        assert "Pre-Computed Rule Violations" in output
        assert "- None" in output
        assert "stage_1" in output
        assert "confidence: 1.0" in output

    def test_to_context_injection_no_arc_stage(self):
        """Test context injection output when no arc stage is matched."""
        flag = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon",
            severity="critical",
        )
        result = DeterministicResult(
            arc_stage=None,
            forbidden_vocab_flags=[flag],
            signature_phrases_found=[],
            has_violations=True,
        )

        output = result.to_context_injection()

        assert "Arc Stage: None" in output
        assert "algorithm" in output
        assert "confidence: 1.0" in output

    def test_to_context_injection_multiple_violations(self):
        """Test context injection with multiple flagged passages."""
        flags = [
            FlaggedPassage(
                text="algorithm",
                reason="Technical jargon",
                severity="critical",
            ),
            FlaggedPassage(
                text="indubitably",
                reason="Too formal",
                severity="critical",
            ),
        ]
        result = DeterministicResult(
            arc_stage=None,
            forbidden_vocab_flags=flags,
            signature_phrases_found=[],
            has_violations=True,
        )

        output = result.to_context_injection()

        assert "algorithm" in output
        assert "indubitably" in output
        assert output.count("FORBIDDEN WORD:") == 2

    def test_to_context_injection_multiple_phrases(self):
        """Test context injection with multiple signature phrases."""
        result = DeterministicResult(
            arc_stage=None,
            forbidden_vocab_flags=[],
            signature_phrases_found=["Water does", "Tide's pulling", "Still and deep"],
            has_violations=False,
        )

        output = result.to_context_injection()

        assert "Water does" in output
        assert "Tide's pulling" in output
        assert "Still and deep" in output
        assert "Signature Phrases Detected:" in output
