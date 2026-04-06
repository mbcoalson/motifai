#!/usr/bin/env python3
"""
Validate chapter frontmatter against schema.

A tool for Nary to call—returns structured JSON for efficient parsing.

Usage:
    python scripts/validate_chapters.py --chapters-dir /path/to/chapters
    python scripts/validate_chapters.py --chapters-dir /path/to/chapters --character "Santiago Esposito"
    python scripts/validate_chapters.py --chapters-dir /path/to/chapters --status draft

Output:
    JSON object with validation results, suitable for LLM consumption.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

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


def extract_frontmatter(file_path: Path) -> tuple[Optional[dict], Optional[str]]:
    """
    Extract YAML frontmatter from a markdown file.
    
    Returns:
        (yaml_dict, error_message) - one will be None
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return None, f"Could not read file: {e}"
    
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None, "No YAML frontmatter found"
    
    try:
        yaml_content = match.group(1)
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            return None, "Frontmatter is not a valid YAML dictionary"
        return data, None
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def validate_chapter(file_path: Path) -> dict:
    """
    Validate a single chapter file.
    
    Returns a dict with:
        - file: filename
        - path: full path
        - valid: bool
        - errors: list of error messages (if invalid)
        - warnings: list of warnings
        - data: parsed frontmatter (if valid)
    """
    result = {
        "file": file_path.name,
        "path": str(file_path),
        "valid": False,
        "errors": [],
        "warnings": [],
        "data": None,
    }
    
    # Extract frontmatter
    yaml_data, error = extract_frontmatter(file_path)
    if error:
        result["errors"].append(error)
        return result
    
    # Validate against schema
    validation_errors = get_validation_errors(yaml_data)
    
    if validation_errors:
        for err in validation_errors:
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Unknown error")
            result["errors"].append(f"{loc}: {msg}")
        return result
    
    # Valid - capture warnings and data
    import warnings
    captured_warnings = []
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        chapter = ChapterFrontmatter(**yaml_data)
        for warning in w:
            captured_warnings.append(str(warning.message))
    
    result["valid"] = True
    result["warnings"] = captured_warnings
    result["data"] = {
        "title": chapter.title,
        "pov_character": chapter.pov_character,
        "status": chapter.status.value,
        "act": chapter.act,
        "chapter_number": chapter.chapter_number,
        "story_date": chapter.story_date.isoformat(),
        "is_groundable": chapter.is_groundable(),
    }
    
    return result


def find_chapter_files(chapters_dir: Path) -> list[Path]:
    """
    Recursively find all .md files in chapters directory.
    
    Excludes files that look like outlines or notes (contain 'Outline' in name
    but don't have DRAFT/REVISED/FINAL).
    """
    files = []
    for md_file in chapters_dir.rglob("*.md"):
        # Skip obvious non-chapters
        name = md_file.name.lower()
        if name.startswith("_") or name.startswith("."):
            continue
        files.append(md_file)
    return sorted(files)


# -----------------------------------------------------------------------------
# Filtering
# -----------------------------------------------------------------------------

def filter_results(
    results: list[dict],
    character: Optional[str] = None,
    status: Optional[str] = None,
    valid_only: bool = False,
    invalid_only: bool = False,
) -> list[dict]:
    """Filter validation results by criteria."""
    filtered = results
    
    if valid_only:
        filtered = [r for r in filtered if r["valid"]]
    
    if invalid_only:
        filtered = [r for r in filtered if not r["valid"]]
    
    if character and valid_only:
        char_lower = character.lower()
        filtered = [
            r for r in filtered 
            if r["data"] and r["data"]["pov_character"].lower() == char_lower
        ]
    
    if status and valid_only:
        filtered = [
            r for r in filtered 
            if r["data"] and r["data"]["status"] == status
        ]
    
    return filtered


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate chapter frontmatter against schema."
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
        default=None,
        help="Filter to specific POV character",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["outline", "draft", "revised", "final"],
        default=None,
        help="Filter to specific status",
    )
    parser.add_argument(
        "--valid-only",
        action="store_true",
        help="Only show valid chapters",
    )
    parser.add_argument(
        "--invalid-only",
        action="store_true",
        help="Only show invalid chapters",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only output summary stats, not per-file details",
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not args.chapters_dir.exists():
        output = {
            "error": f"Directory not found: {args.chapters_dir}",
            "success": False,
        }
        print(json.dumps(output, indent=2))
        sys.exit(1)
    
    # Find and validate all chapter files
    files = find_chapter_files(args.chapters_dir)
    results = [validate_chapter(f) for f in files]
    
    # Apply filters
    filtered = filter_results(
        results,
        character=args.character,
        status=args.status,
        valid_only=args.valid_only,
        invalid_only=args.invalid_only,
    )
    
    # Build summary
    total = len(results)
    valid_count = sum(1 for r in results if r["valid"])
    invalid_count = total - valid_count
    groundable_count = sum(
        1 for r in results 
        if r["valid"] and r["data"] and r["data"]["is_groundable"]
    )
    
    # POV character breakdown (valid chapters only)
    pov_counts = {}
    for r in results:
        if r["valid"] and r["data"]:
            pov = r["data"]["pov_character"]
            pov_counts[pov] = pov_counts.get(pov, 0) + 1
    
    summary = {
        "total_files": total,
        "valid": valid_count,
        "invalid": invalid_count,
        "groundable": groundable_count,
        "by_pov_character": pov_counts,
        "canonical_characters": CANONICAL_CHARACTERS,
    }
    
    # Build output
    output = {
        "success": True,
        "summary": summary,
    }
    
    if not args.summary_only:
        output["chapters"] = filtered
    
    print(json.dumps(output, indent=2))
    
    # Exit with error code if any invalid
    sys.exit(0 if invalid_count == 0 else 1)


if __name__ == "__main__":
    main()
