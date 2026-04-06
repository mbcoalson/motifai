---
tags:
  - WaterRising
  - code
  - tagging
  - hybrid
  - metadata
  - design-doc
aliases:
  - tag_utils_instructions
source_file: src/agent_utilities/tag_utils.py
Date: 2025-03-25
---

# 🧭 Prompt/Instructions for `tag_utils.py` — Expanded Metadata Matching Utility

## 🧠 Purpose
The `tag_utils.py` module is responsible for filtering metadata chunks based on a user’s natural language query, identifying implicit or explicit references to story metadata like characters, themes, tone, chapter titles, and tags.

Its primary function, `filter_by_tag(query: str, metadata: list) -> list`, serves as the metadata understanding layer in a **hybrid retrieval system**, sitting alongside semantic search (FAISS) to ensure relevant story context is returned based on both meaning and metadata alignment.

This function is **evolving** from a tag-matching utility into a fuzzy, multi-field metadata filter, enabling natural conversation with the system without rigid syntax.

---

## 🔍 What the Updated Code Should Accomplish

### ✅ Detect Explicit Metadata References
- Look for `@key:value` syntax (e.g. `@character:Anais`, `@theme:Hope`).
- Match values across these known fields:
  - `title`
  - `tags`
  - `characters`
  - `themes`
  - `tone`
  - (optionally) `summary`

### ✅ Support Fuzzy Matching
- Allow case-insensitive, partial string matches.
  - `@character:anais` matches `[[Anais Non]]`
- Strip out Obsidian link brackets `[[ ]]` during match checks.

### ✅ Support Multiple Metadata Filters
- If the query contains multiple `@key:value` filters, apply them together (match-all logic).
  - `@character:Anais @theme:Hope` matches chunks satisfying both.

### ✅ Return Matching Metadata Chunks
- Return only chunks from the list that satisfy all parsed filters.
- If **no filters** are found in the query, return an **empty list** (to allow semantic fallback).

### ✅ Be Easily Extendable
- Design logic to easily support future fields like `location`, `arc`, or `emotion`.
- Keep modular and human-readable for LLM and agent integration.

---

## 🧩 Integration in the Current System

This module is used as part of **hybrid retrieval** alongside semantic search in:

- [`retrieval_utils.py`](../agent_utilities/retrieval_utils.md)

It powers context filtering for agents like:

- [`writing_coach.py`](../Agents/writing_coach.md) *(Narratus)*
- Future agents:
  - `style_agent.py`
  - `drafting_agent.py`
  - `worldbuilding_agent.py`

Designed to run **before or in parallel with FAISS** to narrow scope for contextual injection.

---

### ⚖️ Contextual Weighting of Fields
- Prioritize more meaningful metadata (e.g., `character` > `tags`).
- Blend FAISS and metadata scores for dynamic ranking.

---

### 📊 Visual or Programmatic Query Plans

Display query breakdown for transparency:

```yaml
Parsed Query:
  - character: Anne
  - tone: Gritty
FAISS Context Matches: 3 chunks
Metadata Matches: 2 chunks

🧠 LangGraph Integration
Use this utility as a metadata pre-check node in the LangGraph agent flow:
flowchart LR
    A[User Query] --> B{Parse for @key:value}
    A --> C[Semantic Search (FAISS)]
    B --> D[filter_by_tag() in tag_utils.py]
    C --> E[Top FAISS Results]
    D --> F[Matching Metadata Chunks]
    E --> G[Merge & Rank Results]
    F --> G
    G --> H[Inject into Prompt]
    H --> I[LLM / Agent Response]

✅ Expected Behavior Summary
Query Example	                Matches What?
@character:Anne	                Any chunk with "[[Anne]]" in characters
@theme:hope	                    themes list includes "Hope" or similar string
@tone:desperate	                tone field contains "desperate"
@tag:#alternative	            tags list includes #alternative
@title:Watcher	                title contains "Watcher"
@character:Anne                 @theme:Hope	Only chunks matching both filters
Hello, I want more about Anais	No explicit filter → filter_by_tag() returns []

🧱 Modular Implementation Plan
We are implementing this system modularly for easier maintenance, testing, and future agent integration.

Directory structure recommendation:
src/agent_utilities/
├── metadata_main.py      # Entrypoint function `filter_by_tag(query, metadata)`
├── tag_parser.py         # Extracts @key:value filters from user input
├── tag_matcher.py        # Applies fuzzy field-by-field matching logic
├── fields/               # (Optional) specialized matchers for custom fields
│   ├── character_matcher.py
│   ├── theme_matcher.py
│   └── ...
├── tests/                # Unit tests for parser, matcher, and integration
│   ├── test_parser.py
│   ├── test_matcher.py
│   └── test_metadata_main.py
└── vision.md             # This file

File Headers Convention: Each module will begin with something like:
"""
Module: tag_parser.py
Purpose: Extract @key:value metadata filters from user queries.

Part of the hybrid retrieval system. This supports the broader goal of making story agents
respond intelligently to user intent by blending natural language and structured metadata.

See: vision.md
"""
Test Naming Convention:

test_returns_empty_list_if_no_explicit_filters() – confirms semantic fallback.

test_parses_character_and_theme_tags_for_hybrid_retrieval() – intention-based expectations.

test_strips_obsidian_links() – ensures fuzzy matching logic works as expected.

🧭 Reminder: Stay Anchored to Purpose
This system isn’t just about parsing queries. It’s about enabling story agents to:

Interpret what the user really wants,

Blend meaning with structure,

And do so in a way that’s extensible, understandable, and agent-compatible.