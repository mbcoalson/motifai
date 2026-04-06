"""Character profile model for voice validation."""
from typing import Optional
from datetime import date
from pathlib import Path
import yaml
from pydantic import BaseModel, ConfigDict, Field

from .arc_stage import ArcStage
from .voice_sample import VoiceSample


class CharacterProfile(BaseModel):
    """
    Represents a character's voice profile for validation.

    This model is designed to be story-agnostic and flexible:
    - REQUIRED: Only the character's name
    - OPTIONAL: All other fields (writers can start minimal and add richness over time)
    - EXTENSIBLE: Allows additional fields via Pydantic's extra="allow"

    The more data provided, the better the validation, but the system works
    with any level of detail (graceful degradation).
    """

    # REQUIRED FIELD
    name: str = Field(..., description="Character's name")

    # OPTIONAL FIELDS
    role: Optional[str] = Field(
        None,
        description="Character's role in the story (e.g., 'protagonist', 'antagonist', 'supporting')"
    )
    basic_traits: Optional[list[str]] = Field(
        None,
        description="Core personality traits (e.g., ['practical', 'blue-collar', 'skeptical'])"
    )
    arc_stages: Optional[list[ArcStage]] = Field(
        None,
        description="Stages of character development with stage-specific voice characteristics"
    )
    voice_samples: Optional[list[VoiceSample]] = Field(
        None,
        description="Example dialogue and narrative samples demonstrating the character's voice"
    )
    contradictions: Optional[list[str]] = Field(
        None,
        description="Internal contradictions or conflicts in the character's personality"
    )
    sensory_filter: Optional[dict[str, int]] = Field(
        None,
        description="Sensory attention weights (e.g., {'touch': 95, 'sound': 70, 'sight': 50})"
    )
    regional_voice: Optional[str] = Field(
        None,
        description="Regional dialect or vernacular (e.g., 'Naples, FL - working-class vernacular')"
    )
    forbidden_vocabulary: Optional[list[str]] = Field(
        None,
        description="Words or phrases the character would never use"
    )
    signature_phrases: Optional[list[str]] = Field(
        None,
        description="Phrases the character frequently uses across all stages"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional fields for story-specific needs

    @classmethod
    def from_yaml_file(cls, yaml_path: Path | str) -> "CharacterProfile":
        """
        Load a CharacterProfile from a YAML file.

        Args:
            yaml_path: Path to the YAML file

        Returns:
            CharacterProfile instance

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML is malformed
            pydantic.ValidationError: If the YAML data doesn't match the model
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Character profile not found: {yaml_path}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return cls(**data)

    @classmethod
    def from_story_config(
        cls,
        story_name: str,
        character_name: str,
        config_base_path: Optional[Path | str] = None
    ) -> "CharacterProfile":
        """
        Load a CharacterProfile from the story-agnostic config structure.

        This is the recommended loading method. It follows the convention:
        config/stories/{story_name}/characters/{character_name}.yaml

        Args:
            story_name: Name of the story (e.g., 'water_rising', 'example_story')
            character_name: Character identifier (e.g., 'santiago_esposito')
            config_base_path: Base path for config directory. If None, uses 'config'
                            relative to current working directory.

        Returns:
            CharacterProfile instance

        Raises:
            FileNotFoundError: If the character profile doesn't exist
            yaml.YAMLError: If the YAML is malformed
            pydantic.ValidationError: If the YAML data doesn't match the model

        Example:
            >>> profile = CharacterProfile.from_story_config(
            ...     story_name='water_rising',
            ...     character_name='santiago_esposito'
            ... )
        """
        if config_base_path is None:
            config_base_path = Path.cwd() / "config"
        else:
            config_base_path = Path(config_base_path)

        yaml_path = (
            config_base_path
            / "stories"
            / story_name
            / "characters"
            / f"{character_name}.yaml"
        )

        return cls.from_yaml_file(yaml_path)

    def get_arc_stage(
        self,
        chapter: Optional[int] = None,
        story_date: Optional[date] = None
    ) -> Optional[ArcStage]:
        """
        Get the appropriate arc stage for a given chapter or story date.

        Args:
            chapter: Chapter number to match against
            story_date: In-story date to match against

        Returns:
            The matching ArcStage, or None if no stages defined or no match found

        Note:
            If both chapter and story_date are provided, chapter takes precedence.
            If multiple stages match, the first match is returned.
        """
        if not self.arc_stages:
            return None

        # Try chapter-based matching first
        if chapter is not None:
            for stage in self.arc_stages:
                if stage.matches_chapter(chapter):
                    return stage

        # Fall back to date-based matching
        if story_date is not None:
            for stage in self.arc_stages:
                if stage.matches_date(story_date):
                    return stage

        return None

    def get_voice_samples_for_stage(self, stage_id: str) -> list[VoiceSample]:
        """
        Get all voice samples associated with a specific arc stage.

        Args:
            stage_id: The stage_id to filter by (e.g., 'stage_1')

        Returns:
            List of VoiceSample objects for the specified stage
        """
        if not self.voice_samples:
            return []

        return [
            sample for sample in self.voice_samples
            if sample.arc_stage == stage_id
        ]

    def has_rich_profile(self) -> bool:
        """
        Check if this profile has rich data (beyond just the name).

        Returns:
            True if profile has at least one optional field populated
        """
        optional_fields = [
            self.role,
            self.basic_traits,
            self.arc_stages,
            self.voice_samples,
            self.contradictions,
            self.sensory_filter,
            self.regional_voice,
            self.forbidden_vocabulary,
            self.signature_phrases
        ]

        return any(field is not None for field in optional_fields)
