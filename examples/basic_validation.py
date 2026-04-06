"""
Basic Voice Validation Example

This example demonstrates how to use the LLM adapters to validate
character voice consistency in text excerpts.

Usage:
    # With Ollama (free, local):
    python examples/basic_validation.py --provider ollama

    # With Claude (requires API key):
    export ANTHROPIC_API_KEY=your-key-here
    python examples/basic_validation.py --provider claude
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.models import CharacterProfile
from src.adapters.llm import create_llm_adapter


def main():
    """Run basic voice validation example."""
    print("=" * 60)
    print("Voice Validation Example")
    print("=" * 60)
    print()

    # 1. Load character profile
    print("Step 1: Loading character profile...")
    profile = CharacterProfile.from_story_config(
        story_name="water_rising",
        character_name="santiago_esposito"
    )
    print(f"✓ Loaded profile for: {profile.name}")
    print(f"  Role: {profile.role}")
    print(f"  Traits: {', '.join(profile.basic_traits or [])}")
    print()

    # 2. Create LLM adapter
    print("Step 2: Creating LLM adapter...")
    # Default to Ollama for local/free testing
    # Change to "claude-sonnet-4.5" to use Claude
    try:
        adapter = create_llm_adapter("qwen2.5-72b")
        print(f"✓ Created {adapter.get_provider()} adapter")
        print(f"  Model: {adapter.get_model_name()}")
    except Exception as e:
        print(f"✗ Failed to create adapter: {e}")
        print("\nTip: Make sure Ollama is running with qwen2.5:72b installed")
        print("Or set ANTHROPIC_API_KEY and use 'claude-sonnet-4.5'")
        return
    print()

    # 3. Check health
    print("Step 3: Checking LLM availability...")
    if adapter.health_check():
        print("✓ LLM is available and responding")
    else:
        print("✗ LLM health check failed")
        print("\nTip: Check that Ollama is running and model is pulled:")
        print("  ollama pull qwen2.5:72b")
        return
    print()

    # 4. Validate good excerpt (matches voice)
    print("Step 4: Validating GOOD excerpt (should pass)...")
    good_excerpt = """
    Santiago leaned against the dock post, the rough wood warm under his palms.
    "Yeah, I seen it," he said. "Tide's been acting weird all week."
    """

    try:
        result = adapter.validate_voice(
            profile=profile,
            excerpt=good_excerpt,
            chapter=1,  # Early arc
            context="Santiago is talking to a fellow dock worker about strange tides"
        )

        print(f"  Status: {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"  Confidence: {result.confidence_score:.1%}")
        print(f"  Severity: {result.severity}")
        if result.summary:
            print(f"  Summary: {result.summary}")
        print()

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return

    # 5. Validate bad excerpt (voice mismatch)
    print("Step 5: Validating BAD excerpt (should fail)...")
    bad_excerpt = """
    Santiago regarded the maritime conditions with considerable trepidation.
    "Indubitably," he articulated, "the oceanographic phenomena have been
    rather unprecedented this fortnight."
    """

    try:
        result = adapter.validate_voice(
            profile=profile,
            excerpt=bad_excerpt,
            chapter=1,
            context="Santiago is talking to a fellow dock worker about strange tides"
        )

        print(f"  Status: {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"  Confidence: {result.confidence_score:.1%}")
        print(f"  Severity: {result.severity}")
        if result.summary:
            print(f"  Summary: {result.summary}")
        print()

        if result.flagged_passages:
            print("  Flagged Issues:")
            for i, issue in enumerate(result.flagged_passages, 1):
                print(f"    {i}. [{issue.severity.upper()}] {issue.text}")
                print(f"       Reason: {issue.reason}")
                if issue.suggestion:
                    print(f"       Suggestion: {issue.suggestion}")
            print()

        if result.suggestions:
            print("  General Suggestions:")
            for suggestion in result.suggestions:
                print(f"    - {suggestion}")
            print()

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return

    # 6. Generate full report
    print("=" * 60)
    print("Full Validation Report")
    print("=" * 60)
    print()
    print(result.to_report())

    print("\n✓ Example complete!")


if __name__ == "__main__":
    main()
