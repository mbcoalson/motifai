"""Deterministic rule-based validation service for character voice."""
from __future__ import annotations

import re
from typing import Optional
from datetime import date
from pydantic import BaseModel

from src.domain.models.character_profile import CharacterProfile
from src.domain.models.validation_result import FlaggedPassage
from src.domain.models.arc_stage import ArcStage


class DeterministicResult(BaseModel):
    """
    Result of deterministic (rule-based) validation with confidence=1.0.

    Contains arc stage information, forbidden vocabulary violations, and
    signature phrases found in the excerpt.
    """

    arc_stage: Optional[ArcStage] = None
    forbidden_vocab_flags: list[FlaggedPassage] = []
    signature_phrases_found: list[str] = []
    has_violations: bool = False

    def to_context_injection(self) -> str:
        """
        Format findings as a string for LLM prompt injection.

        Returns:
            Formatted string with validation findings, confidence=1.0
        """
        lines = []

        # Add violations section if present
        if self.forbidden_vocab_flags:
            lines.append(
                "Pre-Computed Rule Violations (confidence: 1.0):"
            )
            for flag in self.forbidden_vocab_flags:
                lines.append(f"- FORBIDDEN WORD: \"{flag.text}\" — {flag.reason}")
        else:
            lines.append(
                "Pre-Computed Rule Violations (confidence: 1.0):"
            )
            lines.append("- None")

        # Add arc stage
        if self.arc_stage:
            lines.append(
                f"Arc Stage: {self.arc_stage.stage_id} ({self.arc_stage.name})"
            )
        else:
            lines.append("Arc Stage: None")

        # Add signature phrases
        if self.signature_phrases_found:
            phrases_str = ", ".join(
                f'"{phrase}"' for phrase in self.signature_phrases_found
            )
            lines.append(f"Signature Phrases Detected: {phrases_str}")
        else:
            lines.append("Signature Phrases Detected: none")

        return "\n".join(lines)


class DeterministicValidator:
    """
    Pure-Python rule-based validation service.

    Performs case-insensitive whole-word matching for forbidden vocabulary,
    partial matching for signature phrases, and arc stage lookup.
    All results have confidence=1.0.
    """

    def validate(
        self,
        profile: CharacterProfile,
        excerpt: str,
        chapter: Optional[int] = None,
        story_date: Optional[date] = None,
    ) -> DeterministicResult:
        """
        Validate an excerpt against a character profile using deterministic rules.

        Performs:
        - Arc stage lookup via chapter or story_date
        - Forbidden vocabulary detection (case-insensitive, whole-word match)
        - Signature phrase detection (case-insensitive, partial match)

        Args:
            profile: Character profile to validate against
            excerpt: Text excerpt to validate
            chapter: Chapter number for arc stage matching
            story_date: In-story date for arc stage matching

        Returns:
            DeterministicResult with findings (confidence=1.0)
        """
        # Get arc stage
        arc_stage = profile.get_arc_stage(chapter=chapter, story_date=story_date)

        # Check forbidden vocabulary
        forbidden_vocab_flags = self._check_forbidden_vocabulary(
            profile, excerpt
        )

        # Check signature phrases
        signature_phrases_found = self._check_signature_phrases(
            profile, excerpt
        )

        # Determine if there are violations
        has_violations = len(forbidden_vocab_flags) > 0

        return DeterministicResult(
            arc_stage=arc_stage,
            forbidden_vocab_flags=forbidden_vocab_flags,
            signature_phrases_found=signature_phrases_found,
            has_violations=has_violations,
        )

    def _check_forbidden_vocabulary(
        self,
        profile: CharacterProfile,
        excerpt: str,
    ) -> list[FlaggedPassage]:
        """
        Check for forbidden vocabulary in the excerpt.

        Uses case-insensitive whole-word matching:
        re.search(r'\b' + re.escape(word) + r'\b', excerpt, re.IGNORECASE)

        Args:
            profile: Character profile containing forbidden vocabulary
            excerpt: Text to check

        Returns:
            List of FlaggedPassage objects for each forbidden word found
        """
        flags: list[FlaggedPassage] = []

        if not profile.forbidden_vocabulary:
            return flags

        for word in profile.forbidden_vocabulary:
            # Case-insensitive whole-word match
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, excerpt, re.IGNORECASE):
                flag = FlaggedPassage(
                    text=word,
                    reason=(
                        f"'{word}' is in {profile.name}'s forbidden vocabulary"
                    ),
                    severity="critical",
                )
                flags.append(flag)

        return flags

    def _check_signature_phrases(
        self,
        profile: CharacterProfile,
        excerpt: str,
    ) -> list[str]:
        """
        Check for signature phrases in the excerpt.

        Uses case-insensitive partial matching:
        phrase.lower() in excerpt.lower()

        Args:
            profile: Character profile containing signature phrases
            excerpt: Text to check

        Returns:
            List of signature phrases found in the excerpt
        """
        found_phrases: list[str] = []

        if not profile.signature_phrases:
            return found_phrases

        excerpt_lower = excerpt.lower()

        for phrase in profile.signature_phrases:
            if phrase.lower() in excerpt_lower:
                found_phrases.append(phrase)

        return found_phrases
