# Testing Guide

## Unit Tests

Run the unit test suite with pytest:

```bash
pytest tests/unit/
```

The unit tests are self-contained and require no external data or dependencies:

- **Adapters:** LLM factory, Claude/Ollama adapter selection and configuration
- **Domain Models:** Character profiles, arc stages, voice samples, validation models
- **Domain Services:** Deterministic validation, character state validation

All tests use fixtures and mocks. You do not need to provision `data/` to run unit tests.

**Coverage requirement:** 90% minimum (configured in `pyproject.toml`).

Run with coverage report:

```bash
pytest tests/unit/ --cov=src --cov-report=term-missing
```

## End-to-End Pipeline

To run the full writing assistant pipeline, you must provide:

### 1. Chapter Data

Create `data/raw/` directory with Obsidian-style markdown chapters.

Each chapter must include YAML frontmatter with:

```yaml
---
title: "Chapter 1 - Title"
pov_character: Character Name
status: draft
act: 1
chapter_number: 1
story_date: 2042-09-01
summary: Brief chapter summary
---
```

See `docs/chapter-frontmatter-schema.md` for complete schema and validation rules.

**Example structure:**

```
data/raw/
  chapter_1_DRAFT.md
  chapter_2_DRAFT.md
  character_notes.md
```

### 2. Environment Setup

Create `.env` in project root:

```
OPENAI_API_KEY=sk-...
```

Do not commit `.env`. Use `.env.example` as a template if it exists.

### 3. Optional: Character Documentation

Place character markdown files in `data/raw/`:

```
data/raw/
  characters/
    character_1.md
    character_2.md
```

Character files are optional but enable richer retrieval and grounding.

### 4. Running the Pipeline

**Build semantic index from chapters:**

```bash
python scripts/build_character_consciousness.py --chapters-dir data/raw/
```

This creates embeddings and prepares the retrieval layer.

**Run interactive chat:**

```bash
python scripts/query_chapters.py --query "your question"
```

**Validate chapter frontmatter:**

```bash
python scripts/validate_chapters.py --chapters-dir data/raw/
```

## Available Scripts

All scripts are in `scripts/`:

- `build_character_consciousness.py` — Create LLM-optimized character state from sources
- `validate_chapters.py` — Check chapters for schema compliance and missing fields
- `query_chapters.py` — Interactive retrieval queries
- `migrate_chapters.py` — Migrate chapters between different structures (use `--chapters-dir` to specify location)

Run any script with `--help` for options.

## Architecture Reference

For implementation details, see `docs/ARCHITECTURE.md`.

For decision records and design rationale, see `docs/decisions/`.
