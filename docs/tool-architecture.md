---
title: Tool Architecture Specification
created: 2024-12-27
purpose: Define standards for CLI tools that Nary can call
status: proposed
---

# Tool Architecture Specification

## Design Principle

**Scripts do work. Nary interprets.**

Every tool should be callable by an LLM agent with minimal token overhead. Tools handle file I/O, validation, and computation. They return structured data. Nary decides what to do with it.

---

## Interface Contract

### Input: CLI Arguments

All tools accept arguments via `argparse`. Standard patterns:

```bash
# Query/filter tools
python scripts/tool_name.py --filter-field value --another-field value

# Action tools  
python scripts/tool_name.py --action verb --target path

# Always available
python scripts/tool_name.py --help
python scripts/tool_name.py --version
```

**Conventions:**
- Use `--kebab-case` for argument names
- Required args should fail fast with clear error message
- Optional args have sensible defaults
- Accept paths as strings (tool resolves to Path internally)

### Output: JSON to stdout

All tools output JSON to stdout. No exceptions.

```json
{
  "success": true,
  "data": { ... },
  "summary": { ... },
  "errors": [],
  "warnings": []
}
```

**Required fields:**
- `success`: boolean - did the tool complete its task?
- `errors`: list[str] - empty if success, otherwise human-readable errors

**Optional fields:**
- `data`: primary payload (structure varies by tool)
- `summary`: aggregated stats for quick parsing
- `warnings`: non-fatal issues
- `metadata`: tool version, execution time, etc.

**Conventions:**
- Pretty-print with `indent=2` for human debugging
- Dates as ISO strings: `"2042-09-03"`
- Paths as strings (not Path objects)
- Enums as their string values

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation errors (data problems) |
| 2 | Runtime errors (missing files, bad args) |

Nary can check exit code before parsing JSON for fast failure detection.

---

## Error Handling

### Fail Fast, Fail Clearly

```python
# Bad - ambiguous failure
if not path.exists():
    return None

# Good - explicit error in output
if not path.exists():
    output = {
        "success": False,
        "errors": [f"Path not found: {path}"],
        "data": None,
    }
    print(json.dumps(output, indent=2))
    sys.exit(2)
```

### Partial Success

Some tools may partially succeed (e.g., validate 10 files, 2 fail). Use:

```json
{
  "success": true,
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2
  },
  "data": {
    "passed": [...],
    "failed": [...]
  },
  "errors": []
}
```

`success: true` means "tool ran correctly"—not "all data was valid."

---

## Directory Structure

```
WaterRisingProject/
├── scripts/                    # CLI tools Nary calls
│   ├── __init__.py
│   ├── validate_chapters.py
│   ├── query_chapters.py
│   ├── get_chapter_content.py
│   └── ...
├── src/
│   ├── schemas/                # Pydantic models (source of truth)
│   │   ├── __init__.py
│   │   └── chapter_schema.py
│   ├── agent_utilities/        # Shared utilities for scripts
│   │   ├── fields/
│   │   └── ...
│   └── ...
├── docs/
│   ├── tool-architecture.md    # This file
│   ├── chapter-frontmatter-schema.md
│   └── ...
├── tests/
│   └── scripts/                # Tool tests
│       └── test_validate_chapters.py
└── skills/                     # Skill library (separate system)
```

---

## Tool Categories

### 1. Query Tools

Read-only. Filter and retrieve data.

| Tool | Purpose |
|------|---------|
| `query_chapters.py` | Find chapters by metadata |
| `list_characters.py` | List all characters with stats |
| `get_character_state.py` | Character knowledge at story point |

**Output pattern:**
```json
{
  "success": true,
  "summary": { "count": N, ... },
  "data": { "results": [...] }
}
```

### 2. Validation Tools

Check data against schemas. Report errors.

| Tool | Purpose |
|------|---------|
| `validate_chapters.py` | Check frontmatter against schema |
| `validate_skills.py` | Check skill files (future) |

**Output pattern:**
```json
{
  "success": true,
  "summary": { "valid": N, "invalid": M },
  "data": { "results": [...] }
}
```

### 3. Content Tools

Retrieve actual content (higher token cost).

| Tool | Purpose |
|------|---------|
| `get_chapter_content.py` | Full chapter text |
| `get_skill.py` | Full skill definition |

**Output pattern:**
```json
{
  "success": true,
  "data": {
    "metadata": { ... },
    "content": "..."
  }
}
```

Nary should prefer query/validation tools and only call content tools when necessary.

### 4. Mutation Tools

Write data. Require explicit confirmation flags.

| Tool | Purpose |
|------|---------|
| `update_frontmatter.py` | Modify chapter metadata |
| `migrate_chapters.py` | Batch update frontmatter |

**Safety requirements:**
- `--dry-run` flag (default) shows what would change
- `--apply` flag required to actually write
- Output includes before/after diff

**Output pattern:**
```json
{
  "success": true,
  "dry_run": true,
  "changes": [
    {
      "file": "...",
      "field": "...",
      "before": "...",
      "after": "..."
    }
  ]
}
```

---

## Configuration

### Paths

Tools should not hardcode paths. Options:

1. **CLI argument** (preferred for flexibility)
   ```bash
   python scripts/query_chapters.py --chapters-dir /path/to/chapters
   ```

2. **Environment variable** (for defaults)
   ```bash
   export WATER_RISING_CHAPTERS="/path/to/Water_Rising/chapters"
   python scripts/query_chapters.py  # uses env var
   ```

3. **Config file** (for complex settings)
   ```bash
   python scripts/query_chapters.py --config config/paths.yaml
   ```

Precedence: CLI arg > env var > config file > hardcoded default

### Config File Format (if needed)

```yaml
# config/paths.yaml
paths:
  chapters: "/path/to/your/story/chapters"
  skills: "./skills"
  output: "./output"

defaults:
  status_filter: ["draft", "revised", "final"]
```

---

## Logging

Tools should not print logs to stdout (reserved for JSON output).

Use stderr for debug/progress if needed:

```python
import sys

def log(msg):
    print(msg, file=sys.stderr)
```

Or use Python's logging module with stderr handler.

---

## Testing

Each tool should have corresponding tests in `tests/scripts/`.

**Test patterns:**
1. Valid input → correct JSON output
2. Invalid input → appropriate error in JSON
3. Edge cases (empty directories, malformed YAML)
4. Exit codes match expectations

```python
# tests/scripts/test_validate_chapters.py
import subprocess
import json

def test_validate_missing_dir():
    result = subprocess.run(
        ["python", "scripts/validate_chapters.py", "--chapters-dir", "/nonexistent"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["success"] is False
    assert "not found" in output["errors"][0].lower()
```

---

## Nary Integration

### Tool Registry

Nary needs a registry of available tools and their capabilities:

```yaml
# config/tool_registry.yaml
tools:
  validate_chapters:
    script: scripts/validate_chapters.py
    description: "Validate chapter frontmatter against schema"
    args:
      --chapters-dir: "Path to chapters directory (required)"
      --character: "Filter to POV character"
      --status: "Filter to status: outline|draft|revised|final"
      --valid-only: "Only show valid chapters"
      --invalid-only: "Only show invalid chapters"
      --summary-only: "Only output summary, not per-file details"
    returns: "JSON with validation results"
    token_cost: low
    
  get_chapter_content:
    script: scripts/get_chapter_content.py
    description: "Retrieve full chapter text"
    args:
      --chapter-number: "Chapter number (1-30)"
      --file: "Or specify file path directly"
    returns: "JSON with frontmatter and content"
    token_cost: high  # Nary should minimize these calls
```

### Calling Pattern

```python
# Pseudocode for Nary's tool execution
def call_tool(tool_name: str, **kwargs) -> dict:
    registry = load_registry()
    tool = registry[tool_name]
    
    args = [sys.executable, tool["script"]]
    for key, value in kwargs.items():
        args.extend([f"--{key.replace('_', '-')}", str(value)])
    
    result = subprocess.run(args, capture_output=True, text=True)
    return json.loads(result.stdout)
```

---

## Versioning

Tools should support `--version` and include version in output metadata:

```json
{
  "success": true,
  "metadata": {
    "tool": "validate_chapters",
    "version": "0.1.0",
    "executed_at": "2024-12-27T10:30:00Z"
  },
  "data": { ... }
}
```

This helps debug issues when tool behavior changes.

---

## Checklist for New Tools

Before merging a new tool:

- [ ] Follows CLI argument conventions
- [ ] Outputs JSON to stdout (only)
- [ ] Includes `success`, `errors` fields
- [ ] Uses appropriate exit codes
- [ ] Has `--help` documentation
- [ ] Has corresponding test file
- [ ] Added to tool registry
- [ ] Reviewed for token efficiency (minimize data in common paths)

---

## Open Questions

1. **Shared utilities location:** Should common code (YAML parsing, path resolution) live in `src/agent_utilities/` or a new `src/tool_utils/`?

2. **Config file format:** YAML for readability, or JSON for consistency with output?

3. **Async support:** Any tools need async execution for performance?

4. **Caching:** Should query tools cache results? If so, where and how long?

---

## Revision History

| Date | Change |
|------|--------|
| 2024-12-27 | Initial draft |
