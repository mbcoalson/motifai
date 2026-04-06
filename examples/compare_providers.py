"""
Provider Comparison Example

This example demonstrates how to compare different LLM providers
(Claude vs Ollama) for voice validation tasks.

Usage:
    export ANTHROPIC_API_KEY=your-key-here
    python examples/compare_providers.py
"""
import sys
from pathlib import Path
from typing import List
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.models import CharacterProfile, ValidationResult
from src.adapters.llm import create_llm_adapter, list_predefined_models


def run_validation(adapter, profile: CharacterProfile, excerpt: str, chapter: int) -> ValidationResult:
    """Run validation and measure time."""
    start = time.time()
    result = adapter.validate_voice(
        profile=profile,
        excerpt=excerpt,
        chapter=chapter
    )
    elapsed = time.time() - start
    return result, elapsed


def main():
    """Compare multiple LLM providers."""
    print("=" * 80)
    print("LLM Provider Comparison for Voice Validation")
    print("=" * 80)
    print()

    # Load character profile
    print("Loading character profile...")
    profile = CharacterProfile.from_story_config(
        story_name="water_rising",
        character_name="santiago_esposito"
    )
    print(f"✓ Loaded: {profile.name}\n")

    # Test excerpt (intentionally has issues)
    test_excerpt = """
    Santiago contemplated the aquatic environment with considerable apprehension.
    "The meteorological conditions have been quite extraordinary," he remarked
    to his colleague, utilizing unnecessarily sophisticated vocabulary.
    """

    # Models to compare
    models_to_test = [
        "qwen2.5-72b",      # Ollama - Free
        "claude-sonnet-4.5"  # Claude - Paid
    ]

    results = {}

    # Test each model
    for model_name in models_to_test:
        print(f"Testing: {model_name}")
        print("-" * 80)

        try:
            # Create adapter
            adapter = create_llm_adapter(model_name)

            # Health check
            if not adapter.health_check():
                print(f"  ✗ Health check failed - skipping\n")
                continue

            print(f"  ✓ Provider: {adapter.get_provider()}")
            print(f"  ✓ Model: {adapter.get_model_name()}")

            # Run validation
            result, elapsed = run_validation(adapter, profile, test_excerpt, chapter=1)

            results[model_name] = {
                "result": result,
                "elapsed": elapsed,
                "provider": adapter.get_provider()
            }

            # Display results
            print(f"\n  Results:")
            print(f"    Status: {'PASSED' if result.is_valid else 'FAILED'}")
            print(f"    Confidence: {result.confidence_score:.1%}")
            print(f"    Severity: {result.severity}")
            print(f"    Issues found: {result.get_issue_count()}")
            print(f"    Processing time: {result.processing_time_ms:.0f}ms (API)")
            print(f"    Total time: {elapsed:.2f}s")

            if result.flagged_passages:
                print(f"\n  Top Issues:")
                for issue in result.flagged_passages[:3]:
                    print(f"    • [{issue.severity}] {issue.text[:50]}...")
                    print(f"      {issue.reason}")

            print()

        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            continue

    # Comparison summary
    if len(results) >= 2:
        print("=" * 80)
        print("Comparison Summary")
        print("=" * 80)
        print()

        print("Model Performance:")
        print(f"{'Model':<20} {'Provider':<10} {'Valid':<8} {'Confidence':<12} {'Issues':<8} {'Time (s)'}")
        print("-" * 80)

        for model_name, data in results.items():
            result = data["result"]
            elapsed = data["elapsed"]
            provider = data["provider"]

            print(
                f"{model_name:<20} "
                f"{provider:<10} "
                f"{'Yes' if result.is_valid else 'No':<8} "
                f"{result.confidence_score:.1%}          "
                f"{result.get_issue_count():<8} "
                f"{elapsed:.2f}"
            )

        print()
        print("Analysis:")
        print("  • Free (Ollama) models: Fast, good quality, no API costs")
        print("  • Paid (Claude) models: Higher quality, more nuanced analysis")
        print("  • Recommendation: Use Ollama for development, Claude for final review")
        print()

    else:
        print("\nNot enough providers available for comparison")
        print("Tip: Install Ollama and set ANTHROPIC_API_KEY to compare both")

    print("\n✓ Comparison complete!")


if __name__ == "__main__":
    main()
