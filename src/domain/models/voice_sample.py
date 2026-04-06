"""Voice sample model for character dialogue and narrative examples."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VoiceSample(BaseModel):
    """
    A dialogue or narrative sample demonstrating character's voice.

    Used to provide concrete examples of how a character speaks or thinks,
    which can be used for validation and learning.
    """
    text: str = Field(..., description="The dialogue or narrative sample")
    context: Optional[str] = Field(
        None,
        description="Context where this sample occurs (e.g., 'Observing natural phenomena')"
    )
    arc_stage: Optional[str] = Field(
        None,
        description="Which arc stage this sample belongs to (e.g., 'stage_1')"
    )
    chapter: Optional[int] = Field(
        None,
        description="Chapter number where this sample appears"
    )
    tags: Optional[list[str]] = Field(
        None,
        description="Tags for categorizing samples (e.g., 'internal_monologue', 'dialogue', 'observation')"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional fields for story-specific needs
