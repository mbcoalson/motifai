"""
Pydantic schema for chapter frontmatter validation.

This is the source of truth for chapter metadata structure.
See: docs/chapter-frontmatter-schema.md for human-readable documentation.

Usage:
    from schemas.chapter_schema import ChapterFrontmatter
    
    # Validate a dict parsed from YAML frontmatter
    chapter = ChapterFrontmatter(**yaml_data)
    
    # Access validation errors
    try:
        chapter = ChapterFrontmatter(**yaml_data)
    except ValidationError as e:
        print(e.errors())
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum
from datetime import date


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

CANONICAL_CHARACTERS = [
    "Anais Non",
    "Santiago Esposito",
    "Joseph Krutz",
    "Anne",
    "Pastor Wolcott",
    "Angeline Non",  # Anais's mother
]

VALID_ACTS = ["1", "2", "2a", "2b", "3"]


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class ChapterStatus(str, Enum):
    """
    Chapter completion status.
    
    - outline: Scene breakdown, not prose. Exclude from character grounding.
    - draft: First pass prose. Include in character grounding.
    - revised: Edited draft. Include in character grounding.
    - final: Publication-ready. Include in character grounding.
    """
    outline = "outline"
    draft = "draft"
    revised = "revised"
    final = "final"


# -----------------------------------------------------------------------------
# Schema
# -----------------------------------------------------------------------------

class ChapterFrontmatter(BaseModel):
    """
    Validated schema for chapter YAML frontmatter.
    
    Required fields must be present for the chapter to be queryable
    by the retrieval system. Optional fields enhance search and provide
    additional context for character conversations.
    
    Example:
        ---
        title: Chapter 3 - The Fisherman
        pov_character: Santiago Esposito
        status: draft
        act: "1"
        chapter_number: 3
        story_date: 2042-09-03
        summary: |
          Santiago fishes the 10,000 Islands, avoiding church and his 
          father's expectations. His passivity feels like wisdom. It isn't.
        ---
    """
    
    # -------------------------------------------------------------------------
    # Required Fields
    # -------------------------------------------------------------------------
    
    title: str = Field(
        ...,
        description="Chapter title, e.g. 'Chapter 3 - The Fisherman'"
    )
    
    pov_character: str = Field(
        ...,
        description="Primary viewpoint character. Use canonical name."
    )
    
    status: ChapterStatus = Field(
        ...,
        description="Chapter completion status: outline, draft, revised, final"
    )
    
    act: str = Field(
        ...,
        description="Act number: '1', '2', '2a', '2b', or '3'"
    )
    
    chapter_number: int = Field(
        ...,
        ge=1,
        le=30,
        description="Chapter number within the full novel (1-30)"
    )
    
    story_date: date = Field(
        ...,
        description="In-world date when chapter events occur (YYYY-MM-DD)"
    )
    
    summary: str = Field(
        ...,
        min_length=10,
        description="Brief description of chapter events (1-3 sentences)"
    )
    
    # -------------------------------------------------------------------------
    # Optional Fields
    # -------------------------------------------------------------------------
    
    characters: Optional[list[str]] = Field(
        default=None,
        description="All named characters appearing in chapter"
    )
    
    themes: Optional[list[str]] = Field(
        default=None,
        description="Thematic elements explored in chapter"
    )
    
    tone: Optional[str] = Field(
        default=None,
        description="Emotional/stylistic tone, e.g. 'Reflective, introspective'"
    )
    
    word_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Approximate or exact word count"
    )
    
    authored_date: Optional[date] = Field(
        default=None,
        description="When this draft was written or last revised"
    )
    
    tags: Optional[list[str]] = Field(
        default=None,
        description="Additional tags for Obsidian/retrieval"
    )
    
    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    
    @field_validator("act")
    @classmethod
    def validate_act(cls, v: str) -> str:
        """Ensure act is a valid value."""
        v_str = str(v).strip()
        if v_str not in VALID_ACTS:
            raise ValueError(
                f"act must be one of {VALID_ACTS}, got '{v_str}'"
            )
        return v_str
    
    @field_validator("pov_character")
    @classmethod
    def validate_pov_character(cls, v: str) -> str:
        """
        Warn if POV character is not in canonical list.
        
        Does not raise error—allows new characters—but logs warning.
        Returns the value normalized (stripped).
        """
        v_stripped = v.strip()
        if v_stripped not in CANONICAL_CHARACTERS:
            # Import here to avoid circular dependency
            import warnings
            warnings.warn(
                f"POV character '{v_stripped}' not in canonical list. "
                f"Known characters: {CANONICAL_CHARACTERS}",
                UserWarning
            )
        return v_stripped
    
    @field_validator("story_date")
    @classmethod
    def validate_story_date(cls, v: date) -> date:
        """Ensure story date is within the novel's timeline (2042)."""
        if v.year < 2040 or v.year > 2045:
            import warnings
            warnings.warn(
                f"story_date {v} is outside expected range (2040-2045). "
                "Water Rising is set in 2042.",
                UserWarning
            )
        return v
    
    @model_validator(mode="after")
    def validate_pov_in_characters(self):
        """If characters list exists, POV character should be in it."""
        if self.characters is not None:
            # Normalize for comparison
            char_names_lower = [c.lower().strip() for c in self.characters]
            pov_lower = self.pov_character.lower().strip()
            
            if pov_lower not in char_names_lower:
                import warnings
                warnings.warn(
                    f"pov_character '{self.pov_character}' not found in "
                    f"characters list: {self.characters}",
                    UserWarning
                )
        return self
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def is_groundable(self) -> bool:
        """
        Returns True if this chapter should be used for character grounding.
        
        Outlines are excluded—they contain plot plans, not lived experience.
        """
        return self.status in (
            ChapterStatus.draft,
            ChapterStatus.revised,
            ChapterStatus.final
        )
    
    def to_yaml_dict(self) -> dict:
        """
        Export to dict suitable for YAML serialization.
        
        Converts dates to ISO strings and excludes None values.
        """
        data = self.model_dump(exclude_none=True)
        
        # Convert dates to ISO strings
        if "story_date" in data:
            data["story_date"] = data["story_date"].isoformat()
        if "authored_date" in data:
            data["authored_date"] = data["authored_date"].isoformat()
        
        # Convert enum to string
        data["status"] = self.status.value
        
        return data


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def parse_frontmatter(yaml_data: dict) -> ChapterFrontmatter:
    """
    Parse and validate a dict of YAML frontmatter.
    
    Args:
        yaml_data: Dictionary parsed from YAML frontmatter
        
    Returns:
        Validated ChapterFrontmatter instance
        
    Raises:
        pydantic.ValidationError: If validation fails
    """
    return ChapterFrontmatter(**yaml_data)


def get_validation_errors(yaml_data: dict) -> list[dict]:
    """
    Attempt validation and return list of errors (if any).
    
    Args:
        yaml_data: Dictionary parsed from YAML frontmatter
        
    Returns:
        List of error dicts, or empty list if valid
    """
    from pydantic import ValidationError
    
    try:
        ChapterFrontmatter(**yaml_data)
        return []
    except ValidationError as e:
        return e.errors()
