#!/usr/bin/env python3
"""
Build a character's knowledge and emotional state at a specific story point.

Reads all POV chapters up to the specified chapter/date and returns what the
character has experienced. Essential for grounding character conversations.

Usage:
    python scripts/get_character_state.py --chapters-dir /path --character "Santiago Esposito"
    python scripts/get_character_state.py --chapters-dir /path --character "Anais Non" --as-of-chapter 3
    python scripts/get_character_state.py --chapters-dir /path --character "Joseph Krutz" --as-of-date 2042-09-05

Output:
    JSON object with character state grounding data.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional
from datetime import date

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schemas.chapter_schema import ChapterFrontmatter, ChapterStatus, CANONICAL_CHARACTERS


# -----------------------------------------------------------------------------
# Frontmatter Parsing
# -----------------------------------------------------------------------------

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter_and_content(file_path: Path) -> tuple[Optional[dict], Optional[str]]:
    """
    Extract YAML frontmatter and content from a markdown file.

    Returns:
        (frontmatter_dict, content_text) - both can be None on error
    """
    try:
        full_content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    match = FRONTMATTER_PATTERN.match(full_content)
    if not match:
        return None, None

    try:
        yaml_content = match.group(1)
        frontmatter = yaml.safe_load(yaml_content)
        if not isinstance(frontmatter, dict):
            return None, None

        # Extract content (everything after frontmatter)
        content = full_content[match.end():]

        return frontmatter, content
    except yaml.YAMLError:
        return None, None


def find_chapter_files(chapters_dir: Path) -> list[Path]:
    """Recursively find all .md files in chapters directory."""
    files = []
    for md_file in chapters_dir.rglob("*.md"):
        name = md_file.name.lower()
        if name.startswith("_") or name.startswith("."):
            continue
        files.append(md_file)
    return sorted(files)


# -----------------------------------------------------------------------------
# Chapter Filtering
# -----------------------------------------------------------------------------

def is_groundable(frontmatter: dict) -> bool:
    """Check if chapter is usable for character grounding (draft/revised/final)."""
    status = frontmatter.get("status", "").lower()
    return status in ("draft", "revised", "final")


def parse_date(date_value) -> Optional[date]:
    """Parse a date from frontmatter (can be date object or string)."""
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, str):
        try:
            return date.fromisoformat(date_value)
        except ValueError:
            return None
    return None


def get_relevant_chapters(
    all_files: list[Path],
    character: str,
    as_of_chapter: Optional[int] = None,
    as_of_date: Optional[date] = None,
) -> list[dict]:
    """
    Get all groundable POV chapters for a character up to a specific point.

    Args:
        all_files: All chapter files to consider
        character: POV character name (canonical)
        as_of_chapter: Include chapters up to and including this chapter number
        as_of_date: Include chapters up to and including this story date

    Returns:
        List of chapter dicts with: {file, path, frontmatter, content, chapter_number, story_date}
    """
    relevant = []

    for file_path in all_files:
        frontmatter, content = extract_frontmatter_and_content(file_path)

        if not frontmatter or not content:
            continue

        # Must be groundable
        if not is_groundable(frontmatter):
            continue

        # Must match POV character
        pov = frontmatter.get("pov_character", "")
        if pov.lower().strip() != character.lower().strip():
            continue

        chapter_number = frontmatter.get("chapter_number")
        story_date = parse_date(frontmatter.get("story_date"))

        # Apply as-of filters
        if as_of_chapter is not None:
            if chapter_number is None or chapter_number > as_of_chapter:
                continue

        if as_of_date is not None:
            if story_date is None or story_date > as_of_date:
                continue

        relevant.append({
            "file": file_path.name,
            "path": str(file_path),
            "frontmatter": frontmatter,
            "content": content,
            "chapter_number": chapter_number,
            "story_date": story_date,
        })

    # Sort by chapter number, then by story date
    def sort_key(ch):
        return (
            ch["chapter_number"] if ch["chapter_number"] is not None else 999,
            ch["story_date"] if ch["story_date"] is not None else date.max,
        )

    relevant.sort(key=sort_key)

    return relevant


# -----------------------------------------------------------------------------
# Character State Synthesis
# -----------------------------------------------------------------------------

def build_chapter_summary(chapter: dict) -> dict:
    """Build a summary of a single chapter for character state."""
    fm = chapter["frontmatter"]

    summary = {
        "chapter_number": chapter["chapter_number"],
        "story_date": chapter["story_date"].isoformat() if chapter["story_date"] else None,
        "title": fm.get("title"),
        "status": fm.get("status"),
        "summary": fm.get("summary"),
        "characters_present": fm.get("characters", []),
        "word_count": fm.get("word_count"),
        # Include first 500 chars of content for context
        "content_preview": chapter["content"][:500].strip() + "..." if len(chapter["content"]) > 500 else chapter["content"].strip(),
    }

    return summary


def synthesize_character_state(chapters: list[dict], character: str) -> str:
    """
    Create a narrative summary of the character's state based on experienced chapters.

    This is a simple implementation - in the future, this could use an LLM
    to create a more sophisticated synthesis.
    """
    if not chapters:
        return f"{character} has not appeared in any groundable POV chapters yet."

    # For now, create a structured summary
    lines = [
        f"Character: {character}",
        f"Total POV chapters experienced: {len(chapters)}",
        "",
        "Chronological chapter sequence:",
    ]

    for i, ch in enumerate(chapters, 1):
        fm = ch["frontmatter"]
        title = fm.get("title", "Untitled")
        chapter_num = ch["chapter_number"]
        story_date = ch["story_date"].isoformat() if ch["story_date"] else "unknown date"
        summary = fm.get("summary", "")

        lines.append(f"{i}. Chapter {chapter_num}: {title} ({story_date})")
        if summary:
            lines.append(f"   Summary: {summary}")
        lines.append("")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build a character's knowledge and emotional state at a specific story point."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        required=True,
        help="Path to chapters directory",
    )
    parser.add_argument(
        "--character",
        type=str,
        required=True,
        help="Character name (canonical)",
    )
    parser.add_argument(
        "--as-of-chapter",
        type=int,
        default=None,
        help="Ground character at this chapter number (default: latest)",
    )
    parser.add_argument(
        "--as-of-date",
        type=str,
        default=None,
        help="Ground character at this story date (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    # Validate directory exists
    if not args.chapters_dir.exists():
        output = {
            "success": False,
            "errors": [f"Directory not found: {args.chapters_dir}"],
            "data": None,
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)

    # Validate character is canonical
    if args.character not in CANONICAL_CHARACTERS:
        # Try case-insensitive match
        char_lower = args.character.lower()
        matched = [c for c in CANONICAL_CHARACTERS if c.lower() == char_lower]

        if matched:
            # Use canonical name
            canonical_char = matched[0]
        else:
            output = {
                "success": False,
                "errors": [
                    f"Character '{args.character}' not found in canonical character list.",
                    f"Available characters: {', '.join(CANONICAL_CHARACTERS)}"
                ],
                "data": None,
            }
            print(json.dumps(output, indent=2))
            sys.exit(1)
    else:
        canonical_char = args.character

    # Parse as-of-date if provided
    as_of_date = None
    if args.as_of_date:
        try:
            as_of_date = date.fromisoformat(args.as_of_date)
        except ValueError:
            output = {
                "success": False,
                "errors": [f"Invalid date format: {args.as_of_date}. Use YYYY-MM-DD."],
                "data": None,
            }
            print(json.dumps(output, indent=2))
            sys.exit(1)

    # Find all chapter files
    all_files = find_chapter_files(args.chapters_dir)

    # Get relevant chapters for this character
    chapters = get_relevant_chapters(
        all_files,
        canonical_char,
        as_of_chapter=args.as_of_chapter,
        as_of_date=as_of_date,
    )

    # Build chapter summaries
    chapter_summaries = [build_chapter_summary(ch) for ch in chapters]

    # Synthesize character state
    state_summary = synthesize_character_state(chapters, canonical_char)

    # Determine what we grounded at
    grounded_at = {}
    if args.as_of_chapter:
        grounded_at["chapter_number"] = args.as_of_chapter
    if args.as_of_date:
        grounded_at["story_date"] = args.as_of_date
    if not grounded_at:
        grounded_at = "latest"

    # Build output
    output = {
        "success": True,
        "errors": [],
        "data": {
            "character": canonical_char,
            "grounded_at": grounded_at,
            "total_chapters_experienced": len(chapters),
            "chapters_experienced": chapter_summaries,
            "state_summary": state_summary,
        },
    }

    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
