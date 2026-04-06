"""Arc stage model for tracking character voice evolution."""
from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ArcStage(BaseModel):
    """
    Represents a stage in a character's arc with specific voice characteristics.

    Characters evolve throughout a story, and their voice (vocabulary, tone, patterns)
    can change. Each arc stage captures the voice characteristics for a specific
    period in the character's development.
    """
    stage_id: str = Field(
        ...,
        description="Unique identifier for this stage (e.g., 'stage_1', 'act_2_crisis')"
    )
    name: str = Field(
        ...,
        description="Human-readable name for this stage (e.g., 'Pre-transformation skeptic')"
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of this arc stage"
    )
    vocabulary_register: Optional[str] = Field(
        None,
        description="Language register used (e.g., 'formal', 'informal', 'technical', 'working-class')"
    )
    emotional_tone: Optional[list[str]] = Field(
        None,
        description="Emotional qualities during this stage (e.g., ['pragmatic', 'patient', 'reserved'])"
    )
    speech_patterns: Optional[list[str]] = Field(
        None,
        description="Characteristic speech patterns (e.g., ['economy of words', 'plain speech'])"
    )
    typical_phrases: Optional[list[str]] = Field(
        None,
        description="Phrases the character commonly uses in this stage"
    )
    forbidden_patterns: Optional[list[str]] = Field(
        None,
        description="Speech patterns or vocabulary the character would NOT use in this stage"
    )
    chapter_range: Optional[dict[str, int]] = Field(
        None,
        description="Chapter range for this stage (e.g., {'start': 1, 'end': 5})"
    )
    date_range: Optional[dict[str, date]] = Field(
        None,
        description="In-story date range for this stage (e.g., {'start': date(2024, 1, 1), 'end': date(2024, 3, 15)})"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional fields for story-specific needs

    def matches_chapter(self, chapter: int) -> bool:
        """
        Check if this arc stage applies to the given chapter number.

        Args:
            chapter: Chapter number to check

        Returns:
            True if this stage applies to the chapter, False otherwise
        """
        if not self.chapter_range:
            return False

        start = self.chapter_range.get('start')
        end = self.chapter_range.get('end')

        if start is None or end is None:
            return False

        return start <= chapter <= end

    def matches_date(self, story_date: date) -> bool:
        """
        Check if this arc stage applies to the given in-story date.

        Args:
            story_date: In-story date to check

        Returns:
            True if this stage applies to the date, False otherwise
        """
        if not self.date_range:
            return False

        start = self.date_range.get('start')
        end = self.date_range.get('end')

        if start is None or end is None:
            return False

        return start <= story_date <= end
