#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
"""
Demo script for character voice validation.

Usage:
    python scripts/demo_validate.py [--chapter N] [--excerpt "..."] [--no-llm]

Examples:
    python scripts/demo_validate.py --no-llm
    python scripts/demo_validate.py --chapter 3 --excerpt "Santiago analyzed the algorithm."
    python scripts/demo_validate.py --chapter 7
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.models.character_profile import CharacterProfile
from src.domain.services.deterministic_validator import DeterministicValidator
from src.domain.models.validation_result import ValidationResult, FlaggedPassage

# Try to import colorama for colored output
try:
    from colorama import Fore, Style, init
    init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


def colorize(text: str, color: str) -> str:
    """Apply color to text if colorama is available, otherwise return as-is."""
    if not HAS_COLORAMA:
        return text
    return f"{color}{text}{Style.RESET_ALL}"


def print_section_header(title: str) -> None:
    """Print a section header."""
    if HAS_COLORAMA:
        print(colorize(f"{'═' * 70}", Fore.CYAN))
        print(colorize(title, Fore.CYAN))
        print(colorize(f"{'═' * 70}", Fore.CYAN))
    else:
        print("=" * 70)
        print(title)
        print("=" * 70)


def print_deterministic_result(det_result) -> None:
    """Print deterministic validation results."""
    print_section_header("Deterministic Layer")

    # Print forbidden vocab flags
    if det_result.forbidden_vocab_flags:
        for flag in det_result.forbidden_vocab_flags:
            flag_text = f"✗ FORBIDDEN: \"{flag.text}\" ({flag.severity})"
            print(colorize(flag_text, Fore.RED))
    else:
        print(colorize("✓ No forbidden vocabulary detected", Fore.GREEN))

    # Print arc stage
    if det_result.arc_stage:
        arc_text = f"  Arc stage: {det_result.arc_stage.stage_id} ({det_result.arc_stage.name}, ch {det_result.arc_stage.chapter_range['start']}–{det_result.arc_stage.chapter_range['end']})"
        print(colorize(arc_text, Fore.YELLOW))
    else:
        print("  Arc stage: None")

    # Print signature phrases
    if det_result.signature_phrases_found:
        phrases_str = ", ".join(f'"{p}"' for p in det_result.signature_phrases_found)
        print(f"  Signature phrases: {phrases_str}")
    else:
        print("  Signature phrases: none detected")


def create_mock_llm_result(profile, excerpt, chapter: int) -> ValidationResult:
    """Create a mock LLM ValidationResult for --no-llm mode."""
    # For deterministic-only validation, create a result with no additional issues
    return ValidationResult(
        character_name=profile.name,
        excerpt=excerpt,
        is_valid=True,
        confidence_score=1.0,
        severity="passed",
        flagged_passages=None,
        arc_stage_used=None,
        model_used="deterministic-only",
        summary="Deterministic validation only (no LLM call).",
        suggestions=None,
        validation_timestamp=datetime.now(),
        processing_time_ms=None,
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demo script for character voice validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_validate.py --no-llm
  python scripts/demo_validate.py --chapter 7 --excerpt "Water does what water does."
  python scripts/demo_validate.py --chapter 3 --no-llm
        """
    )

    parser.add_argument(
        "--chapter",
        type=int,
        default=3,
        help="Chapter number for arc stage matching (default: 3)"
    )
    parser.add_argument(
        "--excerpt",
        type=str,
        default="Santiago analyzed the algorithm. The methodology was clear.",
        help="Text excerpt to validate (default: 'Santiago analyzed the algorithm. The methodology was clear.')"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM call; use deterministic validation only"
    )

    args = parser.parse_args()

    # Load character profile
    try:
        profile = CharacterProfile.from_story_config(
            story_name="water_rising",
            character_name="santiago_esposito",
            config_base_path=project_root / "config"
        )
    except FileNotFoundError as e:
        print(colorize(f"ERROR: Could not load character profile: {e}", Fore.RED))
        sys.exit(1)

    print(f"Character: {profile.name}")
    print(f"Chapter: {args.chapter}")
    print(f"Excerpt: {args.excerpt}\n")

    # Run deterministic validation
    det_validator = DeterministicValidator()
    det_result = det_validator.validate(
        profile=profile,
        excerpt=args.excerpt,
        chapter=args.chapter
    )

    print_deterministic_result(det_result)

    # Determine final validation result
    if args.no_llm:
        print_section_header("LLM Layer (claude-haiku-3.5)")
        print(colorize("[skipped (--no-llm)]", Fore.YELLOW))

        # Create a mock result with deterministic findings
        final_result = ValidationResult(
            character_name=profile.name,
            excerpt=args.excerpt,
            is_valid=not det_result.has_violations,
            confidence_score=1.0,
            severity="critical" if det_result.has_violations else "passed",
            flagged_passages=det_result.forbidden_vocab_flags if det_result.forbidden_vocab_flags else None,
            arc_stage_used=det_result.arc_stage.stage_id if det_result.arc_stage else None,
            model_used="deterministic-only",
            summary="Deterministic validation only (no LLM call).",
            suggestions=None,
            validation_timestamp=datetime.now(),
            processing_time_ms=None,
        )
    else:
        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print_section_header("LLM Layer (claude-haiku-3.5)")
            print(colorize(
                "ERROR: ANTHROPIC_API_KEY not set. Cannot call LLM.",
                Fore.RED
            ))
            print("Suggestion: Use --no-llm to run deterministic validation only.")
            sys.exit(1)

        # Import LLM components
        try:
            from src.adapters.llm.llm_factory import create_llm_adapter
            from src.domain.services.validation_service import ValidationService
        except ImportError as e:
            print(colorize(f"ERROR: Could not import LLM components: {e}", Fore.RED))
            sys.exit(1)

        print_section_header("LLM Layer (claude-haiku-3.5)")

        try:
            adapter = create_llm_adapter("claude-haiku-3.5", api_key=api_key)
            service = ValidationService(adapter)
            final_result = service.validate(
                profile=profile,
                excerpt=args.excerpt,
                chapter=args.chapter
            )
            print("[LLM validation completed]")
        except Exception as e:
            print(colorize(f"ERROR: LLM validation failed: {e}", Fore.RED))
            sys.exit(1)

    # Print final report
    print()
    print_section_header("Final ValidationResult")
    print(final_result.to_report())


if __name__ == "__main__":
    main()
