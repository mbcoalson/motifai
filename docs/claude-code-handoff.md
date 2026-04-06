# Claude Code Handoff: Character Roleplay System Development

## Session Context

**Latest Session:** 2024-12-28 (4 hours)
**Focus:** Character consciousness simulator for authentic roleplay interactions
**Status:** Phase 1 Complete - Foundation Built

**Previous Session:** 2024-12-27 - SAGE Skill Library Experiment (see bottom of document for original context)

## Project Location

```
C:\Users\mattc\Documents\Path\WaterRisingProject
```

## What Was Built This Session

### 1. Schema Definition
- `src/schemas/chapter_schema.py` — Pydantic model for chapter frontmatter validation
- `src/schemas/__init__.py` — Package init

### 2. CLI Tools
- `scripts/validate_chapters.py` — Validates chapter frontmatter against schema (implemented)
- `scripts/query_chapters.py` — Queries chapters by metadata without loading content (implemented)

### 3. Configuration
- `config/tool_registry.yaml` — Registry of all tools Nary can call, with args and examples
- `docs/tool-architecture.md` — Architecture spec for CLI tools
- `docs/chapter-frontmatter-schema.md` — Human-readable schema documentation

### 4. Skill Library (Started)
- `skills/_index.md` — Skill library overview
- `skills/voice/santiago-conversation.md` — First skill file (character conversation patterns)
- `skills/rollouts/_template.md` — Template for documenting experiments

## What We Built (2024-12-28)

### Character Consciousness Builder

**File:** `scripts/build_character_consciousness.py`

Assembles complete character state from:
- `Characters/` - Voice profiles, gestalt files, character essence
- `chapters/` - Lived experience (POV chapters only)
- `Continuity_Tracking/` - Physical state, relationships (partially implemented)

**Outputs:**
- JSON for LLM (dense character consciousness)
- Markdown for human review
- Cached for fast iteration

**Usage:**
```bash
python scripts/build_character_consciousness.py \
  --character "Santiago Esposito" \
  --date "2042-09-05" \
  --output-json .cache/santiago_consciousness.json
```

### Minimal Prompt Methodology

**Key Discovery:** Don't make LLM "perform" traits. Make it BE the character.

**Prompt Structure:**
```
You ARE [Character Name].

[Where, when, what just happened - situational grounding]

Below is data about your life and experiences. This is YOUR memory.
Reference it when relevant, but respond naturally.

Don't perform traits. Don't announce patterns. Just be.

[CONSCIOUSNESS DATA JSON]

Don't overplay it.
```

### Testing Results

**Santiago Esposito tested at Sept 4, 2042 (Chapter 6)**
- ✅ Foundation works - character responds contextually
- ⚠️ Still feels "overplayed" - overzealous actor quality
- ⚠️ Speech affectations too strong
- ⚠️ Regional voice missing (Naples/FL blend of genteel north + Miami + Cracker culture)

**User Note for Next Session:**
> "Santiago knows more than he feels. May need trait intensity sliders (0-100 scores) to fine-tune without overcontrolling LLM. Consider Stanford study approach - build character through iterative conversation, not pre-programmed traits."

## Immediate Next Steps

**Priority 1: Refinement System**
1. Design trait intensity weighting (0-100 scores)
2. Research Naples/SW Florida regional speech patterns
3. Test longer conversation sessions (30+ min)
4. Complete missing extractors (knowledge bounds, relationships)

**Priority 2: Standalone Tool**
- Build `talk_to_character.py` with API integration
- Session logging and resume
- Transcript export for tuning

**Priority 3: Multi-Character Testing**
- Test Anais with same methodology
- Validate system is character-agnostic

## Detailed Progress

See `docs/character-roleplay-system-progress.md` for full development log.

---

# Original SAGE Experiment Context (2024-12-27)

## What Was Built Previous Session

## What Needs to Happen Next

1. **Run validation** — See current state of chapter frontmatter
2. **Review validation output with user** — Decide which fixes to apply
3. **Build `migrate_chapters.py`** — Tool to batch-fix frontmatter (dry-run by default, --apply to write)
4. **Fix chapter frontmatter** — Add missing fields: `pov_character`, `status`, `act`, `chapter_number`, `story_date`
5. **Build `get_character_state.py`** — Tool to ground characters at specific story points
6. **Test Santiago conversation** — First rollout of the skill library experiment

## Architecture Decisions (Locked)

- **Tools output JSON to stdout** — Nary parses structured output, not prose
- **Mutation tools require --apply flag** — Dry-run by default, user confirms before writing
- **Config precedence:** CLI arg > env var > config file > hardcoded default
- **Scripts in `scripts/`**, shared code in `src/agent_utilities/`
- **No caching** — Dataset is small enough (~2-3 MB at novel completion)
- **Tool registry at `config/tool_registry.yaml`** — Nary checks this before attempting tasks

## Key Files to Read

For context on the schema:
```
src/schemas/chapter_schema.py
docs/chapter-frontmatter-schema.md
```

For context on tool architecture:
```
docs/tool-architecture.md
config/tool_registry.yaml
```

For context on the skill library experiment:
```
skills/_index.md
skills/voice/santiago-conversation.md
```

## Chapter Files Location

```
C:\Users\mattc\Documents\Path\Water_Rising\chapters\Act 1\
```

Current chapters have inconsistent YAML frontmatter. Missing fields include:
- `pov_character` (required for character grounding)
- `status` (in filename but not frontmatter)
- `act` (inferred from folder but not explicit)
- `chapter_number`
- `story_date` (exists but field name varies)

## User Preferences

- Prefers tools over manual file operations
- Wants dry-run previews before mutations
- Uses "Acts" not "Stages" for story structure
- Characters should be grounded in written chapters, not outlines
- Values critical assessment over validation
- Direct communication style

## Conversation Transcript

Full conversation history available at:
```
/mnt/transcripts/2025-12-26-21-39-44-sage-skill-library-experiment-setup.txt
```

This contains detailed discussion of SAGE paper, skill library design, and architecture decisions.
