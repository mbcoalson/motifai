#!/usr/bin/env python3
"""
Update word_count fields in chapter frontmatter with accurate counts.

A tool for Nary to call—counts words in narrative content (excluding frontmatter)
and updates the word_count field. DRY-RUN by default.

Usage:
    python scripts/update_word_counts.py --chapters-dir /path/to/chapters
    python scripts/update_word_counts.py --chapters-dir /path/to/chapters --apply

Output:
    JSON object with word count updates (dry-run) or actual changes (--apply).
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# -----------------------------------------------------------------------------
# Frontmatter Parsing
# -----------------------------------------------------------------------------

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_frontmatter_and_content(file_path: Path) -> tuple[dict, str, str, str]:
    """
    Extract YAML frontmatter and remaining content from a markdown file.

    Returns:
        (yaml_dict, raw_yaml_str, content_after_frontmatter, error_message)
    """
    try:
        full_content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return None, None, None, f"Could not read file: {e}"

    match = FRONTMATTER_PATTERN.match(full_content)
    if not match:
        # No frontmatter
        return {}, "", full_content, None

    try:
        yaml_content = match.group(1)
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            return None, None, None, "Frontmatter is not a valid YAML dictionary"

        # Get content after frontmatter
        content_after = full_content[match.end():]
        return data, yaml_content, content_after, None
    except yaml.YAMLError as e:
        return None, None, None, f"YAML parse error: {e}"


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
# Frontmatter Update
# -----------------------------------------------------------------------------

def update_word_count_in_frontmatter(
    yaml_data: dict,
    actual_word_count: int
) -> tuple[dict, dict]:
    """
    Update word_count field in frontmatter.

    Returns:
        (updated_yaml_data, change_dict or None)
    """
    updated = yaml_data.copy()
    old_count = updated.get("word_count")

    # Update the count
    updated["word_count"] = actual_word_count

    # Build change dict if different
    if old_count != actual_word_count:
        change = {
            "field": "word_count",
            "before": old_count,
            "after": actual_word_count,
            "difference": actual_word_count - (old_count or 0)
        }
        return updated, change

    return updated, None


def write_frontmatter(file_path: Path, frontmatter: dict, content_after: str) -> None:
    """
    Write updated frontmatter back to file.

    Preserves content after frontmatter.
    """
    from datetime import date

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
        description="Update word_count fields in chapter frontmatter. DRY-RUN by default."
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
    all_updates = []
    files_changed = 0

    for file_path in files:
        yaml_data, raw_yaml, content_after, error = extract_frontmatter_and_content(file_path)

        if error:
            all_updates.append({
                "file": file_path.name,
                "path": str(file_path),
                "error": error,
                "change": None
            })
            continue

        # Count words in narrative content
        actual_word_count = count_words(content_after)

        # Update frontmatter
        updated_data, change = update_word_count_in_frontmatter(yaml_data, actual_word_count)

        file_result = {
            "file": file_path.name,
            "path": str(file_path),
            "actual_word_count": actual_word_count,
            "change": change
        }

        if change:
            files_changed += 1

            # Write if --apply flag is set
            if args.apply:
                try:
                    write_frontmatter(file_path, updated_data, content_after)
                    file_result["written"] = True
                except Exception as e:
                    file_result["write_error"] = str(e)
                    file_result["written"] = False

        all_updates.append(file_result)

    # Build summary
    summary = {
        "total_files": len(files),
        "files_needing_updates": files_changed,
        "files_unchanged": len(files) - files_changed,
    }

    if args.apply:
        written_count = sum(1 for u in all_updates if u.get("written", False))
        summary["files_written"] = written_count
        summary["write_errors"] = files_changed - written_count

    # Build output
    output = {
        "success": True,
        "dry_run": not args.apply,
        "summary": summary,
        "updates": all_updates,
    }

    print(json.dumps(output, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
