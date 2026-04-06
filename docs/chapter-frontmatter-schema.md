---
title: Chapter Frontmatter Schema
created: 2024-12-27
purpose: Standardize YAML frontmatter for Water Rising chapters to enable reliable retrieval and character grounding
status: proposed
---

# Chapter Frontmatter Schema

## Purpose

Consistent frontmatter enables:
1. **Character conversation grounding:** "Talk to Santiago" finds all Santiago POV chapters
2. **Status filtering:** Only pull from draft or final chapters, ignore outlines
3. **Act/chapter navigation:** Scope queries to specific parts of the story
4. **Retrieval efficiency:** Query by metadata without loading full text

---

## Schema Definition

### Required Fields

```yaml
---
title: "Chapter 3 - The Fisherman"
pov_character: Santiago Esposito
status: draft
act: 1
chapter_number: 3
story_date: 2042-09-03
summary: |
  One to three sentences describing what happens in this chapter.
---
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Chapter title (matches filename minus status suffix) |
| `pov_character` | string | Primary viewpoint character. Use canonical name. |
| `status` | enum | One of: `outline`, `draft`, `revised`, `final` |
| `act` | integer | Act number: `1`, `2a`, `2b`, `3` |
| `chapter_number` | integer | Chapter number within the full novel |
| `story_date` | date | In-world date (YYYY-MM-DD format) |
| `summary` | string | Brief description of chapter events |

### Optional Fields

```yaml
characters:
  - Santiago Esposito
  - Santiago's father
  - Santiago's mother
themes:
  - Passive resistance
  - Faith questioning
tone: Reflective, introspective
word_count: 650
authored_date: 2025-09-29
tags:
  - WaterRising
---
```

| Field | Type | Description |
|-------|------|-------------|
| `characters` | list | All named characters appearing in chapter |
| `themes` | list | Thematic elements explored |
| `tone` | string | Emotional/stylistic tone |
| `word_count` | integer | Approximate or exact word count |
| `authored_date` | date | When you wrote/last revised this draft |
| `tags` | list | Additional tags for Obsidian/retrieval |

---

## Field Details

### pov_character

**Canonical Names (use exactly):**
- `Anais Non` (avoid special characters for query reliability)
- `Santiago Esposito` (not Jacob, not Chris)
- `Joseph Krutz`
- `Anne`

**Why separate from characters list?**
- `characters` lists everyone in the scene
- `pov_character` identifies whose head we're in
- Character conversations need POV specifically

### status

| Value | Meaning |
|-------|---------|
| `outline` | Scene breakdown, not prose. Exclude from character grounding. |
| `draft` | First pass prose. Include in character grounding. |
| `revised` | Edited draft. Include in character grounding. |
| `final` | Publication-ready. Include in character grounding. |

**Retrieval logic:** Character conversations draw only from draft, revised, or final. Outlines contain plot plans, not lived experience.

### story_date

In-world date when the chapter events occur. ISO format: `2042-09-03`

Enables:
- Timeline queries ("What has Santiago experienced by September 5th?")
- Continuity checking
- Character state grounding at specific story moments

### act

Options:
- Simple: `1`, `2`, `3`
- Detailed: `1`, `2a`, `2b`, `3`

Use whichever matches your mental model.

---

## Integration with Retrieval System

### Query Examples

Using existing tag_parser.py syntax:

```
@pov_character:santiago              -> All Santiago POV chapters
@pov_character:santiago @status:draft -> Santiago drafts only
@act:1 @status:draft                  -> All Act 1 drafts
@character:joseph                     -> All chapters featuring Joseph
```

### Required Update to tag_matcher.py

Current alias_map needs expansion:

```python
alias_map = {
    "character": "characters",
    "theme": "themes",
    "tag": "tags",
    "pov": "pov_character",      # Add
    "chapter": "chapter_number", # Add
}
```

---

## Migration from Current State

### Current Inconsistencies

| Issue | Chapters Affected | Fix |
|-------|-------------------|-----|
| No `pov_character` field | All | Add field, infer from title/characters |
| `Date` field ambiguous | Ch 2, Ch 3 | Split into `story_date` and `authored_date` |
| Old character names in tags | Ch 3 (Jacob) | Update to canonical names |
| Status in filename only | All | Add `status` field to frontmatter |
| Missing `act` field | All | Add based on folder location |
| Missing `chapter_number` | All | Add based on filename |

---

## Example Migration: Chapter 3

**Before:**
```yaml
---
Date: 2025-09-29
characters:
  - Santiago
  - Santiago's mother
  - Santiago's father
date: 01/04/2024
summary: The story revolves around a young man named Santiago...
tags:
  - Jacob
  - WaterRising
  - "#Chapter4"
  - writing
  - drafts
themes:
  - Individualism vs Conformity
  - Nature vs Society
  - Religious questioning
title: Chapter 3 - The Fisherman
tone: Reflective and introspective
word_count: ~650
---
```

**After:**
```yaml
---
title: Chapter 3 - The Fisherman
pov_character: Santiago Esposito
status: draft
act: 1
chapter_number: 3
story_date: 2042-09-03
summary: |
  Santiago fishes the 10,000 Islands, avoiding church and his father's 
  expectations. His passivity feels like wisdom. It isn't.
characters:
  - Santiago Esposito
  - Santiago's father
  - Santiago's mother
themes:
  - Passive resistance
  - Faith questioning
  - Nature as refuge
tone: Reflective, introspective
word_count: 650
authored_date: 2025-09-29
tags:
  - WaterRising
---
```

**Changes:**
- Added: pov_character, status, act, chapter_number, story_date
- Removed: duplicate/conflicting Date/date fields
- Removed: stale Jacob tag
- Fixed: #Chapter4 tag error (was Chapter 3)
- Used: canonical name Santiago Esposito
- Cleaned: summary

---

## Decision Points

1. **Act numbering:** Use `1, 2, 3` or `1, 2a, 2b, 3`?
2. **Filename convention:** Keep status in filename, or frontmatter only?
3. **Character names:** Full name (`Santiago Esposito`) or first name (`Santiago`)?
4. **Migration approach:** All chapters now, or incrementally as touched?

---

## Next Steps (If Approved)

1. Finalize schema based on your feedback
2. Write migration audit script (flags issues, no auto-fix)
3. Review audit output together
4. Apply fixes manually or via assisted script
5. Update tag_matcher.py alias map
6. Test retrieval with new schema
