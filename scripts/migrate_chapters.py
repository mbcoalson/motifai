#!/usr/bin/env python3
"""
Migrate chapter frontmatter to match schema.

A tool for Nary to call—automatically infers and fixes missing required fields.
DRY-RUN by default - requires --apply flag to actually write changes.

Usage:
    python scripts/migrate_chapters.py --chapters-dir /path/to/chapters
    python scripts/migrate_chapters.py --chapters-dir /path/to/chapters --apply

Output:
    JSON object with proposed changes (dry-run) or actual changes (--apply).
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

from schemas.chapter_schema import (
    ChapterFrontmatter,
    ChapterStatus,
    CANONICAL_CHARACTERS,
    get_validation_errors,
)


# -----------------------------------------------------------------------------
# Frontmatter Parsing
# -----------------------------------------------------------------------------

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter_and_content(file_path: Path) -> tuple[Optional[dict], Optional[str], Optional[str]]:
    """
    Extract YAML frontmatter and remaining content from a markdown file.

    Returns:
        (yaml_dict, content_after_frontmatter, error_message)
    """
    try:
        full_content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return None, None, f"Could not read file: {e}"

    match = FRONTMATTER_PATTERN.match(full_content)
    if not match:
        # No frontmatter - we'll need to create it
        return {}, full_content, None

    try:
        yaml_content = match.group(1)
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            return None, None, "Frontmatter is not a valid YAML dictionary"

        # Get content after frontmatter
        content_after = full_content[match.end():]
        return data, content_after, None
    except yaml.YAMLError as e:
        return None, None, f"YAML parse error: {e}"


# -----------------------------------------------------------------------------
# Word Counting
# -----------------------------------------------------------------------------

def count_words(text: str) -> int:
    """
    Count words in narrative text.

    Removes:
    - Markdown formatting
    - HTML comments
    - Code blocks
    - Excessive whitespace

    Counts actual words.
    """
    # Remove HTML comments (common in Obsidian)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)

    # Remove markdown links but keep the text
    # [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove markdown images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # Remove markdown headers (#, ##, etc.)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic markers but keep text
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_

    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Split on whitespace and count non-empty tokens
    words = text.split()
    return len(words)


# -----------------------------------------------------------------------------
# Field Inference
# -----------------------------------------------------------------------------

def infer_status_from_filename(filename: str) -> Optional[str]:
    """Extract status from filename like 'Chapter 1 - Title - DRAFT.md'."""
    filename_upper = filename.upper()
    if "FINAL" in filename_upper:
        return "final"
    if "REVISED" in filename_upper:
        return "revised"
    if "DRAFT" in filename_upper:
        return "draft"
    if "OUTLINE" in filename_upper:
        return "outline"
    return None


def infer_chapter_number_from_filename(filename: str) -> Optional[int]:
    """Extract chapter number from filename like 'Chapter 3 - Title.md'."""
    match = re.search(r"Chapter\s+(\d+)", filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def infer_pov_from_title_or_filename(filename: str, title: Optional[str] = None) -> Optional[str]:
    """
    Infer POV character from title or filename.

    Looks for canonical character names in the title or filename.
    """
    search_text = f"{filename} {title or ''}".lower()

    # Check for canonical character names (case insensitive)
    for character in CANONICAL_CHARACTERS:
        # Check first name or full name
        first_name = character.split()[0].lower()
        full_name = character.lower()

        if full_name in search_text or first_name in search_text:
            return character

    # Special handling for common variations
    if "anais" in search_text or "anaïs" in search_text:
        return "Anais Non"
    if "santiago" in search_text or "jacob" in search_text:
        return "Santiago Esposito"
    if "joseph" in search_text or "krutz" in search_text:
        return "Joseph Krutz"
    if "anne" in search_text and "non" not in search_text:
        return "Anne"
    if "pastor" in search_text or "wolcott" in search_text:
        return "Pastor Wolcott"
    if "angeline" in search_text or "mother" in search_text:
        return "Angeline Non"

    return None


def infer_act_from_path(file_path: Path) -> Optional[str]:
    """Extract act from directory structure like '.../Act 1/...'."""
    path_str = str(file_path)

    # Look for "Act N" in the path
    match = re.search(r"Act\s+(\d+[ab]?)", path_str, re.IGNORECASE)
    if match:
        return match.group(1).lower()

    return None


def normalize_date_field(value) -> Optional[date]:
    """
    Attempt to parse various date formats into a date object.

    Handles:
    - ISO format: 2042-09-03
    - US format: 09/03/2042
    - Ambiguous formats
    """
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    # Try ISO format first
    try:
        return date.fromisoformat(value)
    except (ValueError, AttributeError):
        pass

    # Try common US formats
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"]:
        try:
            from datetime import datetime
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def clean_character_name(name: str) -> str:
    """
    Clean character name - remove Obsidian links and normalize.

    Converts: "[[Santiago Esposito]]" -> "Santiago Esposito"
    """
    # Remove Obsidian link syntax
    name = re.sub(r'\[\[(.*?)\]\]', r'\1', name)
    return name.strip()


def normalize_word_count(value) -> Optional[int]:
    """
    Convert word_count to integer.

    Handles: "~3,000", "3000", 3000
    """
    if isinstance(value, int):
        return value

    if not isinstance(value, str):
        return None

    # Remove ~, commas, and whitespace
    cleaned = re.sub(r'[~,\s]', '', value)

    try:
        return int(cleaned)
    except ValueError:
        return None


# -----------------------------------------------------------------------------
# Migration Logic
# -----------------------------------------------------------------------------

def serialize_for_json(value):
    """Convert date objects to ISO strings for JSON serialization."""
    if isinstance(value, date):
        return value.isoformat()
    return value


def migrate_frontmatter(
    file_path: Path,
    yaml_data: dict,
    content_after_frontmatter: str,
) -> tuple[dict, list[dict]]:
    """
    Migrate frontmatter to match schema.

    Returns:
        (migrated_data, changes_list)
    """
    changes = []
    migrated = yaml_data.copy()

    # Infer and add missing required fields

    # 1. pov_character
    if "pov_character" not in migrated:
        inferred_pov = infer_pov_from_title_or_filename(
            file_path.name,
            migrated.get("title")
        )
        if inferred_pov:
            migrated["pov_character"] = inferred_pov
            changes.append({
                "field": "pov_character",
                "before": None,
                "after": inferred_pov,
                "method": "inferred from filename/title"
            })

    # 2. status
    if "status" not in migrated:
        inferred_status = infer_status_from_filename(file_path.name)
        if inferred_status:
            migrated["status"] = inferred_status
            changes.append({
                "field": "status",
                "before": None,
                "after": inferred_status,
                "method": "inferred from filename"
            })

    # 3. act
    if "act" not in migrated:
        inferred_act = infer_act_from_path(file_path)
        if inferred_act:
            migrated["act"] = inferred_act
            changes.append({
                "field": "act",
                "before": None,
                "after": inferred_act,
                "method": "inferred from directory path"
            })

    # 4. chapter_number
    if "chapter_number" not in migrated:
        inferred_chapter = infer_chapter_number_from_filename(file_path.name)
        if inferred_chapter:
            migrated["chapter_number"] = inferred_chapter
            changes.append({
                "field": "chapter_number",
                "before": None,
                "after": inferred_chapter,
                "method": "inferred from filename"
            })

    # 5. story_date - try to extract from existing date fields
    if "story_date" not in migrated:
        # Look for Date or date field
        for key in ["Date", "date", "story_date"]:
            if key in migrated and key != "story_date":
                parsed_date = normalize_date_field(migrated[key])
                if parsed_date:
                    migrated["story_date"] = parsed_date
                    changes.append({
                        "field": "story_date",
                        "before": serialize_for_json(migrated[key]),
                        "after": parsed_date.isoformat(),
                        "method": f"migrated from '{key}' field"
                    })
                    break

    # Fix existing fields that need normalization

    # Calculate accurate word_count from narrative content
    actual_word_count = count_words(content_after_frontmatter)
    old_word_count = migrated.get("word_count")

    if old_word_count != actual_word_count:
        changes.append({
            "field": "word_count",
            "before": old_word_count,
            "after": actual_word_count,
            "method": "calculated from narrative content"
        })
        migrated["word_count"] = actual_word_count

    # Clean up character names (remove Obsidian links)
    if "characters" in migrated and isinstance(migrated["characters"], list):
        cleaned_chars = [clean_character_name(c) for c in migrated["characters"]]
        if cleaned_chars != migrated["characters"]:
            changes.append({
                "field": "characters",
                "before": migrated["characters"],
                "after": cleaned_chars,
                "method": "removed Obsidian link syntax"
            })
            migrated["characters"] = cleaned_chars

    # Normalize pov_character if it has Obsidian syntax
    if "pov_character" in migrated:
        cleaned_pov = clean_character_name(migrated["pov_character"])
        if cleaned_pov != migrated["pov_character"]:
            changes.append({
                "field": "pov_character",
                "before": migrated["pov_character"],
                "after": cleaned_pov,
                "method": "removed Obsidian link syntax"
            })
            migrated["pov_character"] = cleaned_pov

    # Remove duplicate/legacy date fields
    legacy_fields = []
    for key in ["Date", "date"]:
        if key in migrated and "story_date" in migrated:
            legacy_fields.append(key)

    for field in legacy_fields:
        changes.append({
            "field": field,
            "before": serialize_for_json(migrated[field]),
            "after": None,
            "method": "removed duplicate (migrated to story_date)"
        })
        del migrated[field]

    # Normalize story_date to date object if it's a string
    if "story_date" in migrated and isinstance(migrated["story_date"], str):
        parsed = normalize_date_field(migrated["story_date"])
        if parsed:
            migrated["story_date"] = parsed

    # Normalize authored_date if present
    if "authored_date" in migrated and isinstance(migrated["authored_date"], str):
        parsed = normalize_date_field(migrated["authored_date"])
        if parsed:
            migrated["authored_date"] = parsed

    return migrated, changes


def write_frontmatter(file_path: Path, frontmatter: dict, content_after: str) -> None:
    """
    Write updated frontmatter back to file.

    Preserves content after frontmatter.
    """
    # Convert date objects to ISO strings for YAML
    yaml_data = frontmatter.copy()
    for key in ["story_date", "authored_date"]:
        if key in yaml_data and isinstance(yaml_data[key], date):
            yaml_data[key] = yaml_data[key].isoformat()

    # Generate YAML
    yaml_str = yaml.dump(
        yaml_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )

    # Write file
    new_content = f"---\n{yaml_str}---\n{content_after}"
    file_path.write_text(new_content, encoding="utf-8")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate chapter frontmatter to match schema. DRY-RUN by default."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        required=True,
        help="Path to chapters directory",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write changes (default: dry-run only)",
    )

    args = parser.parse_args()

    # Validate directory exists
    if not args.chapters_dir.exists():
        output = {
            "success": False,
            "errors": [f"Directory not found: {args.chapters_dir}"],
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)

    # Find all markdown files
    files = sorted(args.chapters_dir.rglob("*.md"))

    # Filter out hidden files and system files
    files = [f for f in files if not f.name.startswith("_") and not f.name.startswith(".")]

    if not files:
        output = {
            "success": False,
            "errors": [f"No markdown files found in {args.chapters_dir}"],
        }
        print(json.dumps(output, indent=2))
        sys.exit(2)

    # Process each file
    all_changes = []
    files_changed = 0

    for file_path in files:
        yaml_data, content_after, error = extract_frontmatter_and_content(file_path)

        if error:
            all_changes.append({
                "file": file_path.name,
                "path": str(file_path),
                "error": error,
                "changes": []
            })
            continue

        # Migrate frontmatter
        migrated_data, changes = migrate_frontmatter(file_path, yaml_data, content_after)

        if changes:
            files_changed += 1

            # Validate migrated data
            validation_errors = get_validation_errors(migrated_data)

            file_result = {
                "file": file_path.name,
                "path": str(file_path),
                "changes": changes,
                "valid_after_migration": len(validation_errors) == 0,
                "remaining_errors": [
                    f"{'.'.join(str(x) for x in err.get('loc', []))}: {err.get('msg', 'Unknown error')}"
                    for err in validation_errors
                ] if validation_errors else []
            }

            # Write if --apply flag is set
            if args.apply:
                try:
                    write_frontmatter(file_path, migrated_data, content_after)
                    file_result["written"] = True
                except Exception as e:
                    file_result["write_error"] = str(e)
                    file_result["written"] = False

            all_changes.append(file_result)

    # Build summary
    summary = {
        "total_files": len(files),
        "files_needing_changes": files_changed,
        "files_unchanged": len(files) - files_changed,
    }

    if args.apply:
        written_count = sum(1 for c in all_changes if c.get("written", False))
        summary["files_written"] = written_count
        summary["write_errors"] = files_changed - written_count

    # Build output
    output = {
        "success": True,
        "dry_run": not args.apply,
        "summary": summary,
        "changes": all_changes,
    }

    print(json.dumps(output, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
