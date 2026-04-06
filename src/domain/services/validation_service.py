"""ValidationService orchestrator: deterministic pre-check followed by LLM validation."""
from __future__ import annotations

from datetime import date
from typing import Optional

from src.domain.models.character_profile import CharacterProfile
from src.domain.models.validation_result import FlaggedPassage, ValidationResult
from src.domain.services.deterministic_validator import DeterministicValidator
from src.ports.llm_adapter import LLMAdapter


class ValidationService:
    """Orchestrates deterministic pre-check followed by LLM validation.

    Runs the deterministic validator first, injects its findings into the
    LLM prompt context, calls the LLM adapter, and merges both result sets
    into a single ValidationResult. Deterministic flags with severity
    'critical' are deduplicated against LLM flags; the LLM entry wins when
    the same forbidden word is flagged by both.
    """

    def __init__(self, llm_adapter: LLMAdapter) -> None:
        """Initialize with an LLM adapter.

        Args:
            llm_adapter: Concrete LLMAdapter implementation used for voice validation.
        """
        self._llm_adapter = llm_adapter

    def validate(
        self,
        profile: CharacterProfile,
        excerpt: str,
        chapter: Optional[int] = None,
        story_date: Optional[date] = None,
        scene_context: Optional[str] = None,
    ) -> ValidationResult:
        """Run deterministic checks then LLM validation, merge results.

        Orchestration steps:
        1. Run DeterministicValidator and capture arc/vocab/phrase findings.
        2. Build an enriched context string from scene_context and deterministic
           findings, joined with a blank line when both are present.
        3. Call the LLM adapter's validate_voice() with the enriched context.
        4. Merge flagged passages: deterministic forbidden-vocab flags that are
           already represented in the LLM result are dropped; remaining
           deterministic flags are prepended to the LLM flags list.
        5. Recompute is_valid from the merged flag list (any critical flag
           makes the result invalid). When the merged list is empty the LLM's
           own is_valid is preserved.

        Args:
            profile: Character profile to validate against.
            excerpt: Text excerpt to validate.
            chapter: Chapter number for arc stage matching (optional).
            story_date: In-story date for arc stage matching (optional).
            scene_context: Additional scene context to inject into the LLM prompt
                (optional).

        Returns:
            A ValidationResult with all scalar fields from the LLM result and
            a merged flagged_passages list.
        """
        # Step 1: deterministic pre-check
        deterministic_validator = DeterministicValidator()
        deterministic_result = deterministic_validator.validate(
            profile, excerpt, chapter, story_date
        )

        # Step 2: build pre_context from deterministic findings, keep scene_context separate.
        # pre_context surfaces under the dedicated "Pre-Computed Rule Violations" header in
        # the prompt, which instructs the LLM not to re-flag items deterministic already caught.
        pre_context: str = deterministic_result.to_context_injection()

        # Step 3: call the LLM adapter — scene_context as context, deterministic as pre_context
        llm_result: ValidationResult = self._llm_adapter.validate_voice(
            profile=profile,
            excerpt=excerpt,
            chapter=chapter,
            context=scene_context,
            pre_context=pre_context,
        )

        # Step 4: merge flagged passages
        llm_flags: list[FlaggedPassage] = list(llm_result.flagged_passages or [])

        # Collect the text values from LLM flags for deduplication (case-insensitive)
        llm_flag_texts: set[str] = {f.text.lower() for f in llm_flags}

        non_duplicate_det_flags: list[FlaggedPassage] = []
        for det_flag in deterministic_result.forbidden_vocab_flags:
            if det_flag.text.lower() not in llm_flag_texts:
                non_duplicate_det_flags.append(det_flag)
            # If the LLM already flagged this word, its entry wins — skip the deterministic one.

        merged_flags: list[FlaggedPassage] = non_duplicate_det_flags + llm_flags

        # Step 5: recompute is_valid
        if merged_flags:
            is_valid: bool = not any(f.severity == "critical" for f in merged_flags)
        else:
            is_valid = llm_result.is_valid

        # Step 6: return merged ValidationResult preserving all LLM scalar fields
        return ValidationResult(
            character_name=llm_result.character_name,
            excerpt=llm_result.excerpt,
            is_valid=is_valid,
            confidence_score=llm_result.confidence_score,
            severity=llm_result.severity,
            flagged_passages=merged_flags if merged_flags else None,
            arc_stage_used=llm_result.arc_stage_used,
            model_used=llm_result.model_used,
            summary=llm_result.summary,
            suggestions=llm_result.suggestions,
            validation_timestamp=llm_result.validation_timestamp,
            processing_time_ms=llm_result.processing_time_ms,
        )
