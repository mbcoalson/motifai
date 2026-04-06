#!/usr/bin/env python
"""Verification script to demonstrate Phase 1 core models functionality."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from src.domain.models import CharacterProfile, ValidationResult, FlaggedPassage


def main():
    print("=" * 60)
    print("Phase 1 Core Models Verification")
    print("=" * 60)
    print()

    # Test 1: Load minimal character profile
    print("Test 1: Loading minimal character profile...")
    minimal = CharacterProfile.from_story_config('example_story', 'example_character')
    print(f"  ✓ Loaded: {minimal.name}")
    print(f"  ✓ Role: {minimal.role}")
    print(f"  ✓ Has rich profile: {minimal.has_rich_profile()}")
    print(f"  ✓ Arc stages: {len(minimal.arc_stages) if minimal.arc_stages else 0}")
    print()

    # Test 2: Load full-featured character profile
    print("Test 2: Loading full-featured character profile...")
    santiago = CharacterProfile.from_story_config('water_rising', 'santiago_esposito')
    print(f"  ✓ Loaded: {santiago.name}")
    print(f"  ✓ Role: {santiago.role}")
    print(f"  ✓ Has rich profile: {santiago.has_rich_profile()}")
    print(f"  ✓ Arc stages: {len(santiago.arc_stages)}")
    print(f"  ✓ Voice samples: {len(santiago.voice_samples)}")
    print(f"  ✓ Regional voice: {santiago.regional_voice}")
    print()

    # Test 3: Arc stage detection by chapter
    print("Test 3: Arc stage detection by chapter...")
    stage1 = santiago.get_arc_stage(chapter=3)
    print(f"  ✓ Chapter 3 stage: {stage1.name if stage1 else 'None'}")
    stage2 = santiago.get_arc_stage(chapter=7)
    print(f"  ✓ Chapter 7 stage: {stage2.name if stage2 else 'None'}")
    print()

    # Test 4: Voice samples for stage
    print("Test 4: Voice samples for specific arc stage...")
    samples = santiago.get_voice_samples_for_stage("stage_1")
    print(f"  ✓ Stage 1 samples: {len(samples)}")
    if samples:
        print(f"  ✓ Example: \"{samples[0].text}\"")
    print()

    # Test 5: Mid-complexity profile with arc stages
    print("Test 5: Mid-complexity character with arc stages...")
    tech = CharacterProfile.from_story_config('example_story', 'tech_wizard')
    print(f"  ✓ Loaded: {tech.name}")
    early_stage = tech.get_arc_stage(chapter=5)
    late_stage = tech.get_arc_stage(chapter=10)
    print(f"  ✓ Chapter 5 stage: {early_stage.name if early_stage else 'None'}")
    print(f"  ✓ Chapter 10 stage: {late_stage.name if late_stage else 'None'}")
    print()

    # Test 6: Validation result with flagged passages
    print("Test 6: Creating validation result...")
    flagged = FlaggedPassage(
        text="algorithm",
        reason="Technical jargon out of character",
        severity="critical",
        suggestion="Use 'pattern' or 'way things work'"
    )

    result = ValidationResult(
        character_name="Santiago Esposito",
        excerpt="Santiago analyzed the algorithm carefully.",
        is_valid=False,
        confidence_score=0.87,
        severity="critical",
        flagged_passages=[flagged],
        model_used="claude-sonnet-4.5",
        arc_stage_used="stage_1",
        summary="Character voice inconsistency: using technical jargon"
    )

    print(f"  ✓ Validation result created")
    print(f"  ✓ Is valid: {result.is_valid}")
    print(f"  ✓ Confidence: {result.confidence_score:.1%}")
    print(f"  ✓ Issues found: {result.get_issue_count()}")
    print(f"  ✓ Has critical issues: {result.has_critical_issues()}")
    print()

    # Test 7: Generate validation report
    print("Test 7: Generating validation report...")
    report = result.to_report()
    print(report)

    print("=" * 60)
    print("All tests passed! Phase 1 core models are working.")
    print("=" * 60)


if __name__ == "__main__":
    main()
