"""Unit tests for CharacterProfile and related models."""
import pytest
from datetime import date
from pathlib import Path

from src.domain.models import (
    CharacterProfile,
    ArcStage,
    VoiceSample,
    ValidationResult,
    FlaggedPassage,
)


class TestVoiceSample:
    """Tests for VoiceSample model."""

    def test_voice_sample_minimal(self):
        """Test creating a voice sample with just required fields."""
        sample = VoiceSample(text="Water does what water does")
        assert sample.text == "Water does what water does"
        assert sample.context is None
        assert sample.arc_stage is None

    def test_voice_sample_full(self):
        """Test creating a voice sample with all fields."""
        sample = VoiceSample(
            text="Tide's pulling harder than usual",
            context="Observing ocean from dock",
            arc_stage="stage_1",
            chapter=2,
            tags=["observation", "working_knowledge"]
        )
        assert sample.text == "Tide's pulling harder than usual"
        assert sample.context == "Observing ocean from dock"
        assert sample.arc_stage == "stage_1"
        assert sample.chapter == 2
        assert "observation" in sample.tags


class TestArcStage:
    """Tests for ArcStage model."""

    def test_arc_stage_minimal(self):
        """Test creating an arc stage with just required fields."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early stage"
        )
        assert stage.stage_id == "stage_1"
        assert stage.name == "Early stage"
        assert stage.description is None

    def test_arc_stage_full(self):
        """Test creating an arc stage with all fields."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Pre-transformation skeptic",
            description="Before the water consciousness emerges",
            vocabulary_register="informal/working-class",
            emotional_tone=["pragmatic", "patient"],
            speech_patterns=["economy of words", "plain speech"],
            typical_phrases=["Water does what water does"],
            forbidden_patterns=["technical jargon"],
            chapter_range={"start": 1, "end": 5}
        )
        assert stage.stage_id == "stage_1"
        assert stage.vocabulary_register == "informal/working-class"
        assert "pragmatic" in stage.emotional_tone
        assert stage.chapter_range["start"] == 1

    def test_matches_chapter_within_range(self):
        """Test that arc stage matches chapter within range."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early",
            chapter_range={"start": 1, "end": 5}
        )
        assert stage.matches_chapter(1) is True
        assert stage.matches_chapter(3) is True
        assert stage.matches_chapter(5) is True

    def test_matches_chapter_outside_range(self):
        """Test that arc stage doesn't match chapter outside range."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early",
            chapter_range={"start": 1, "end": 5}
        )
        assert stage.matches_chapter(0) is False
        assert stage.matches_chapter(6) is False
        assert stage.matches_chapter(100) is False

    def test_matches_chapter_no_range(self):
        """Test that arc stage without chapter_range doesn't match."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early"
        )
        assert stage.matches_chapter(1) is False

    def test_matches_date_within_range(self):
        """Test that arc stage matches date within range."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early",
            date_range={
                "start": date(2024, 1, 1),
                "end": date(2024, 3, 31)
            }
        )
        assert stage.matches_date(date(2024, 1, 1)) is True
        assert stage.matches_date(date(2024, 2, 15)) is True
        assert stage.matches_date(date(2024, 3, 31)) is True

    def test_matches_date_outside_range(self):
        """Test that arc stage doesn't match date outside range."""
        stage = ArcStage(
            stage_id="stage_1",
            name="Early",
            date_range={
                "start": date(2024, 1, 1),
                "end": date(2024, 3, 31)
            }
        )
        assert stage.matches_date(date(2023, 12, 31)) is False
        assert stage.matches_date(date(2024, 4, 1)) is False


class TestCharacterProfile:
    """Tests for CharacterProfile model."""

    def test_character_profile_minimal(self):
        """Test creating a character profile with just a name."""
        profile = CharacterProfile(name="Detective Murphy")
        assert profile.name == "Detective Murphy"
        assert profile.role is None
        assert profile.basic_traits is None
        assert profile.arc_stages is None
        assert profile.has_rich_profile() is False

    def test_character_profile_with_basic_traits(self):
        """Test creating a character profile with basic traits."""
        profile = CharacterProfile(
            name="Detective Murphy",
            role="protagonist",
            basic_traits=["gruff", "cynical", "drinks too much"]
        )
        assert profile.name == "Detective Murphy"
        assert profile.role == "protagonist"
        assert "gruff" in profile.basic_traits
        assert profile.has_rich_profile() is True

    def test_character_profile_with_arc_stages(self):
        """Test creating a character profile with arc stages."""
        stage1 = ArcStage(
            stage_id="stage_1",
            name="Early",
            chapter_range={"start": 1, "end": 5}
        )
        stage2 = ArcStage(
            stage_id="stage_2",
            name="Late",
            chapter_range={"start": 6, "end": 10}
        )

        profile = CharacterProfile(
            name="Santiago",
            arc_stages=[stage1, stage2]
        )

        assert len(profile.arc_stages) == 2
        assert profile.arc_stages[0].stage_id == "stage_1"

    def test_get_arc_stage_by_chapter(self):
        """Test retrieving the correct arc stage by chapter."""
        stage1 = ArcStage(
            stage_id="stage_1",
            name="Early",
            chapter_range={"start": 1, "end": 5}
        )
        stage2 = ArcStage(
            stage_id="stage_2",
            name="Late",
            chapter_range={"start": 6, "end": 10}
        )

        profile = CharacterProfile(
            name="Santiago",
            arc_stages=[stage1, stage2]
        )

        assert profile.get_arc_stage(chapter=3).stage_id == "stage_1"
        assert profile.get_arc_stage(chapter=7).stage_id == "stage_2"
        assert profile.get_arc_stage(chapter=100) is None

    def test_get_arc_stage_by_date(self):
        """Test retrieving the correct arc stage by story date."""
        stage1 = ArcStage(
            stage_id="stage_1",
            name="Early",
            date_range={
                "start": date(2024, 1, 1),
                "end": date(2024, 3, 31)
            }
        )
        stage2 = ArcStage(
            stage_id="stage_2",
            name="Late",
            date_range={
                "start": date(2024, 4, 1),
                "end": date(2024, 6, 30)
            }
        )

        profile = CharacterProfile(
            name="Santiago",
            arc_stages=[stage1, stage2]
        )

        assert profile.get_arc_stage(story_date=date(2024, 2, 15)).stage_id == "stage_1"
        assert profile.get_arc_stage(story_date=date(2024, 5, 1)).stage_id == "stage_2"
        assert profile.get_arc_stage(story_date=date(2024, 12, 1)) is None

    def test_get_arc_stage_no_stages(self):
        """Test get_arc_stage returns None when no stages defined."""
        profile = CharacterProfile(name="Murphy")
        assert profile.get_arc_stage(chapter=1) is None
        assert profile.get_arc_stage(story_date=date(2024, 1, 1)) is None

    def test_get_voice_samples_for_stage(self):
        """Test retrieving voice samples for a specific stage."""
        sample1 = VoiceSample(
            text="Early dialogue",
            arc_stage="stage_1"
        )
        sample2 = VoiceSample(
            text="Late dialogue",
            arc_stage="stage_2"
        )
        sample3 = VoiceSample(
            text="Another early dialogue",
            arc_stage="stage_1"
        )

        profile = CharacterProfile(
            name="Santiago",
            voice_samples=[sample1, sample2, sample3]
        )

        stage1_samples = profile.get_voice_samples_for_stage("stage_1")
        assert len(stage1_samples) == 2
        assert all(s.arc_stage == "stage_1" for s in stage1_samples)

        stage2_samples = profile.get_voice_samples_for_stage("stage_2")
        assert len(stage2_samples) == 1

    def test_get_voice_samples_no_samples(self):
        """Test get_voice_samples_for_stage returns empty list when no samples."""
        profile = CharacterProfile(name="Murphy")
        assert profile.get_voice_samples_for_stage("stage_1") == []

    def test_has_rich_profile(self):
        """Test has_rich_profile correctly identifies rich vs minimal profiles."""
        minimal = CharacterProfile(name="Murphy")
        assert minimal.has_rich_profile() is False

        with_role = CharacterProfile(name="Murphy", role="protagonist")
        assert with_role.has_rich_profile() is True

        with_traits = CharacterProfile(
            name="Murphy",
            basic_traits=["gruff"]
        )
        assert with_traits.has_rich_profile() is True


class TestCharacterProfileLoading:
    """Tests for CharacterProfile YAML loading."""

    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create a temporary config directory structure."""
        config = tmp_path / "config"
        water_rising = config / "stories" / "water_rising" / "characters"
        example_story = config / "stories" / "example_story" / "characters"

        water_rising.mkdir(parents=True)
        example_story.mkdir(parents=True)

        return config

    def test_from_yaml_file_minimal(self, tmp_path):
        """Test loading minimal profile from YAML file."""
        yaml_file = tmp_path / "murphy.yaml"
        yaml_content = """
name: Detective Murphy
role: protagonist
basic_traits:
  - gruff
  - cynical
"""
        yaml_file.write_text(yaml_content)

        profile = CharacterProfile.from_yaml_file(yaml_file)
        assert profile.name == "Detective Murphy"
        assert profile.role == "protagonist"
        assert "gruff" in profile.basic_traits

    def test_from_yaml_file_with_arc_stages(self, tmp_path):
        """Test loading profile with arc stages from YAML."""
        yaml_file = tmp_path / "santiago.yaml"
        yaml_content = """
name: Santiago Esposito
role: protagonist
arc_stages:
  - stage_id: stage_1
    name: Early stage
    chapter_range:
      start: 1
      end: 5
  - stage_id: stage_2
    name: Late stage
    chapter_range:
      start: 6
      end: 10
"""
        yaml_file.write_text(yaml_content)

        profile = CharacterProfile.from_yaml_file(yaml_file)
        assert profile.name == "Santiago Esposito"
        assert len(profile.arc_stages) == 2
        assert profile.arc_stages[0].stage_id == "stage_1"
        assert profile.arc_stages[0].chapter_range["start"] == 1

    def test_from_yaml_file_not_found(self, tmp_path):
        """Test that loading non-existent file raises FileNotFoundError."""
        yaml_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            CharacterProfile.from_yaml_file(yaml_file)

    def test_from_story_config(self, config_dir):
        """Test loading profile using story-agnostic config structure."""
        santiago_yaml = (
            config_dir / "stories" / "water_rising" / "characters" / "santiago_esposito.yaml"
        )
        yaml_content = """
name: Santiago Esposito
role: protagonist
basic_traits:
  - practical
  - blue-collar
"""
        santiago_yaml.write_text(yaml_content)

        profile = CharacterProfile.from_story_config(
            story_name="water_rising",
            character_name="santiago_esposito",
            config_base_path=config_dir
        )

        assert profile.name == "Santiago Esposito"
        assert profile.role == "protagonist"
        assert "practical" in profile.basic_traits

    def test_from_story_config_not_found(self, config_dir):
        """Test that loading non-existent story config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CharacterProfile.from_story_config(
                story_name="nonexistent_story",
                character_name="nonexistent_character",
                config_base_path=config_dir
            )


class TestFlaggedPassage:
    """Tests for FlaggedPassage model."""

    def test_flagged_passage_minimal(self):
        """Test creating flagged passage with required fields."""
        passage = FlaggedPassage(
            text="Santiago used the word 'algorithm'",
            reason="Character would not use technical jargon",
            severity="critical"
        )
        assert passage.text == "Santiago used the word 'algorithm'"
        assert passage.severity == "critical"
        assert passage.suggestion is None

    def test_flagged_passage_with_suggestion(self):
        """Test creating flagged passage with suggestion."""
        passage = FlaggedPassage(
            text="algorithm",
            reason="Too technical for Santiago's voice",
            severity="critical",
            suggestion="Replace with plain language like 'pattern' or 'way things work'"
        )
        assert passage.suggestion is not None
        assert "plain language" in passage.suggestion


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_validation_result_passed(self):
        """Test creating a passing validation result."""
        result = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Tide's pulling harder than usual.",
            is_valid=True,
            confidence_score=0.95,
            severity="passed",
            model_used="claude-sonnet-4.5"
        )
        assert result.is_valid is True
        assert result.confidence_score == 0.95
        assert result.severity == "passed"
        assert result.has_critical_issues() is False

    def test_validation_result_failed(self):
        """Test creating a failed validation result."""
        flagged = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon",
            severity="critical"
        )

        result = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Santiago analyzed the algorithm.",
            is_valid=False,
            confidence_score=0.85,
            severity="critical",
            flagged_passages=[flagged],
            model_used="claude-sonnet-4.5"
        )

        assert result.is_valid is False
        assert result.has_critical_issues() is True
        assert result.get_issue_count() == 1

    def test_get_critical_issues(self):
        """Test filtering critical issues from flagged passages."""
        critical = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon",
            severity="critical"
        )
        moderate = FlaggedPassage(
            text="commenced",
            reason="Too formal",
            severity="moderate"
        )
        info = FlaggedPassage(
            text="really",
            reason="Weak word",
            severity="info"
        )

        result = ValidationResult(
            character_name="Santiago",
            excerpt="Test",
            is_valid=False,
            confidence_score=0.7,
            flagged_passages=[critical, moderate, info],
            model_used="claude-sonnet-4.5"
        )

        critical_issues = result.get_critical_issues()
        assert len(critical_issues) == 1
        assert critical_issues[0].severity == "critical"

    def test_to_report(self):
        """Test generating text report from validation result."""
        flagged = FlaggedPassage(
            text="algorithm",
            reason="Technical jargon",
            severity="critical",
            suggestion="Use 'pattern' or 'way things work'"
        )

        result = ValidationResult(
            character_name="Santiago Esposito",
            excerpt="Santiago analyzed the algorithm.",
            is_valid=False,
            confidence_score=0.85,
            severity="critical",
            flagged_passages=[flagged],
            model_used="claude-sonnet-4.5",
            arc_stage_used="stage_1",
            summary="Character voice inconsistency detected"
        )

        report = result.to_report()
        assert "Santiago Esposito" in report
        assert "FAILED" in report
        assert "85.00%" in report
        assert "algorithm" in report
        assert "Technical jargon" in report
