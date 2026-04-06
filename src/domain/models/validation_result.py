"""Validation result model for character voice validation output."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FlaggedPassage(BaseModel):
    """
    Represents a specific passage flagged during validation.

    Contains the problematic text, the reason it was flagged,
    severity level, and optional suggestions for correction.
    """
    text: str = Field(..., description="The flagged text passage")
    reason: str = Field(..., description="Why this passage was flagged")
    severity: str = Field(
        ...,
        description="Severity level: 'critical', 'moderate', 'info'"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggested correction or improvement"
    )
    line_number: Optional[int] = Field(
        None,
        description="Line number where the passage appears (if available)"
    )
    context: Optional[str] = Field(
        None,
        description="Surrounding context for the flagged passage"
    )

    model_config = ConfigDict(extra="allow")


class ValidationResult(BaseModel):
    """
    Result of validating a text excerpt against a character's voice profile.

    This model captures all relevant information about the validation,
    including whether it passed, confidence scores, specific issues found,
    and actionable suggestions.
    """
    character_name: str = Field(
        ...,
        description="Name of the character being validated against"
    )
    excerpt: str = Field(
        ...,
        description="The text excerpt that was validated"
    )
    is_valid: bool = Field(
        ...,
        description="Overall validation result (True = passed, False = issues found)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the validation result (0.0 to 1.0)"
    )
    severity: Optional[str] = Field(
        None,
        description="Overall severity: 'passed', 'info', 'moderate', 'critical'"
    )
    flagged_passages: Optional[list[FlaggedPassage]] = Field(
        None,
        description="Specific passages that were flagged with issues"
    )
    arc_stage_used: Optional[str] = Field(
        None,
        description="Which arc stage was used for validation (if applicable)"
    )
    model_used: str = Field(
        ...,
        description="LLM model used for validation (e.g., 'claude-sonnet-4.5', 'qwen2.5-72b-ollama')"
    )
    summary: Optional[str] = Field(
        None,
        description="Human-readable summary of the validation results"
    )
    suggestions: Optional[list[str]] = Field(
        None,
        description="General suggestions for improving the text"
    )
    validation_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the validation was performed"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to perform validation (in milliseconds)"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional fields for model-specific metadata

    def get_critical_issues(self) -> list[FlaggedPassage]:
        """
        Get all flagged passages with 'critical' severity.

        Returns:
            List of critically flagged passages
        """
        if not self.flagged_passages:
            return []

        return [
            passage for passage in self.flagged_passages
            if passage.severity == 'critical'
        ]

    def get_issue_count(self) -> int:
        """
        Get the total number of flagged passages.

        Returns:
            Number of flagged passages
        """
        return len(self.flagged_passages) if self.flagged_passages else 0

    def has_critical_issues(self) -> bool:
        """
        Check if there are any critical issues.

        Returns:
            True if there are critical issues, False otherwise
        """
        return len(self.get_critical_issues()) > 0

    def to_report(self) -> str:
        """
        Generate a human-readable text report of the validation results.

        Returns:
            Formatted string report
        """
        lines = [
            f"Validation Report: {self.character_name}",
            "=" * 60,
            f"Status: {'PASSED' if self.is_valid else 'FAILED'}",
            f"Confidence: {self.confidence_score:.2%}",
            f"Severity: {self.severity or 'N/A'}",
            f"Model: {self.model_used}",
            f"Arc Stage: {self.arc_stage_used or 'N/A'}",
            f"Timestamp: {self.validation_timestamp.isoformat()}",
            "",
        ]

        if self.summary:
            lines.extend([
                "Summary:",
                self.summary,
                "",
            ])

        if self.flagged_passages:
            lines.append(f"Issues Found: {len(self.flagged_passages)}")
            lines.append("")

            for i, passage in enumerate(self.flagged_passages, 1):
                lines.extend([
                    f"Issue #{i} [{passage.severity.upper()}]",
                    f"Text: {passage.text}",
                    f"Reason: {passage.reason}",
                ])
                if passage.suggestion:
                    lines.append(f"Suggestion: {passage.suggestion}")
                lines.append("")

        if self.suggestions:
            lines.append("General Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")

        return "\n".join(lines)
