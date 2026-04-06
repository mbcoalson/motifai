#!/usr/bin/env python3
"""
Query chapters by metadata without loading full content.

The PRIMARY tool for chapter discovery. Returns frontmatter only.
Use this before get_chapter_content to minimize token usage.

Usage:
    python scripts/query_chapters.py --chapters-dir /path/to/chapters
    python scripts/query_chapters.py --chapters-dir /path --pov "Santiago Esposito"
    python scripts/query_chapters.py --chapters-dir /path --status draft --act 1

Output:
    JSON object with matching chapters (metadata only).
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

from schemas.chapter_schema import ChapterFrontmatter, ChapterStatus


# -----------------------------------------------------------------------------
# Frontmatter Parsing
# -----------------------------------------------------------------------------

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter(file_path: Path) -> Optional[dict]:
    """
    Extract YAML frontmatter from a markdown file.
    Returns None if no valid frontmatter found.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None
    
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None
    
    try:
        yaml_content = match.group(1)
        data = yaml.safe_load(yaml_content)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    
    return None


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
# Query Logic
# -----------------------------------------------------------------------------

def matches_filters(
    frontmatter: dict,
    pov: Optional[str] = None,
    status: Optional[str] = None,
    act: Optional[str] = None,
    chapter: Optional[int] = None,
    groundable_only: bool = False,
) -> bool:
    """Check if frontmatter matches all provided filters."""
    
    # POV character filter
    if pov:
        fm_pov = frontmatter.get("pov_character", "")
        if fm_pov.lower().strip() != pov.lower().strip():
            return False
    
    # Status filter
    if status:
        fm_status = frontmatter.get("status", "")
        if fm_status.lower().strip() != status.lower().strip():
            return False
    
    # Act filter
    if act:
        fm_act = str(frontmatter.get("act", ""))
        if fm_act.lower().strip() != act.lower().strip():
            return False
    
    # Chapter number filter
    if chapter is not None:
        fm_chapter = frontmatter.get("chapter_number")
        if fm_chapter != chapter:
            return False
    
    # Groundable filter (draft, revised, or final only)
    if groundable_only:
        fm_status = frontmatter.get("status", "").lower()
        if fm_status not in ("draft", "revised", "final"):
            return False
    
    return True


def build_chapter_result(file_path: Path, frontmatter: dict) -> dict:
    """Build a result object for a single chapter."""
    # Extract key fields for summary (avoid returning entire frontmatter blob)
    result = {
        "file": file_path.name,
        "path": str(file_path),
        "frontmatter": {
            "title": frontmatter.get("title"),
            "pov_character": frontmatter.get("pov_character"),
            "status": frontmatter.get("status"),
            "act": frontmatter.get("act"),
            "chapter_number": frontmatter.get("chapter_number"),
            "story_date": frontmatter.get("story_date"),
            "summary": frontmatter.get("summary"),
        }
    }
    
    # Convert date to string if it's a date object
    if result["frontmatter"]["story_date"]:
        story_date = result["frontmatter"]["story_date"]
        if hasattr(story_date, "isoformat"):
            result["frontmatter"]["story_date"] = story_date.isoformat()
        else:
            result["frontmatter"]["story_date"] = str(story_date)
    
    return result


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Query chapters by metadata without loading full content."
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        required=True,
        help="Path to chapters directory",
    )
    parser.add_argument(
        "--pov",
        type=str,
        default=None,
        help="Filter by POV character",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["outline", "draft", "revised", "final"],
        default=None,
        help="Filter by status",
    )
    parser.add_argument(
        "--act",
        type=str,
        choices=["1", "2", "2a", "2b", "3"],
        default=None,
        help="Filter by act",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        default=None,
        help="Filter by chapter number",
    )
    parser.add_argument(
        "--groundable-only",
        action="store_true",
        help="Only return chapters usable for character grounding (draft/revised/final)",
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
    
    # Find all chapter files
    files = find_chapter_files(args.chapters_dir)
    
    # Query chapters
    results = []
    skipped_no_frontmatter = 0
    
    for file_path in files:
        frontmatter = extract_frontmatter(file_path)
        
        if not frontmatter:
            skipped_no_frontmatter += 1
            continue
        
        if matches_filters(
            frontmatter,
            pov=args.pov,
            status=args.status,
            act=args.act,
            chapter=args.chapter,
            groundable_only=args.groundable_only,
        ):
            results.append(build_chapter_result(file_path, frontmatter))
    
    # Build filters applied summary
    filters_applied = {}
    if args.pov:
        filters_applied["pov_character"] = args.pov
    if args.status:
        filters_applied["status"] = args.status
    if args.act:
        filters_applied["act"] = args.act
    if args.chapter:
        filters_applied["chapter_number"] = args.chapter
    if args.groundable_only:
        filters_applied["groundable_only"] = True
    
    # Build output
    output = {
        "success": True,
        "errors": [],
        "summary": {
            "total_files_scanned": len(files),
            "matches": len(results),
            "skipped_no_frontmatter": skipped_no_frontmatter,
            "filters_applied": filters_applied if filters_applied else "none",
        },
        "chapters": results,
    }
    
    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
