# WaterRising Project - Start Here

## For Claude Code / AI Assistants

**🔴 IMPORTANT: Read these files first**:
1. **`project-state.json`** - Current progress, decisions, blockers, notes
2. **`docs/INDEX.md`** - Documentation navigation and project overview

### Workflow
1. Read `project-state.json` to understand current state
2. Read `docs/INDEX.md` to understand structure
3. Navigate to relevant docs based on user's question
4. **Update `project-state.json` after significant work** (remind user to keep it current!)

---

## For Developers (Human)

### What You Can Say (Natural Language)

**You don't need to be precise!** Examples:

- "What do I need to do first?"
- "Let's implement this"
- "Which model should I use?"
- "How much will this cost?"
- "Show me use cases"
- "What's Phase 3?"
- "Help me configure this"

See full list in [Common Tasks](#common-tasks--what-to-say) below.

### Quick Start Commands

```bash
cd c:\Users\mattc\Documents\Path\WaterRisingProject
python -m venv .venv
.venv\Scripts\activate
pip install poetry
poetry install
```

---

## Project Overview

**What**: Multi-model AI voice validation for character consistency in Water Rising novel

**How**: LLM-based validation (local Qwen/Llama or cloud Claude/GPT) with hexagonal architecture

**Timeline**: 14 weeks, 7 phases → See [docs/implementation/README.md](docs/implementation/README.md)

**Current Status**: Check `project-state.json`

---

## Documentation Structure

```
docs/INDEX.md              ← Master navigation (START HERE)
├── rogue-integration/     ← Voice validation system (use cases, architecture)
├── model-testing/         ← Multi-model benchmarking (model matrix, scenarios)
├── cost-analysis/         ← Pricing & budgets (API costs, SaaS tiers)
├── implementation/        ← 14-week plan (phase-by-phase guide)
├── configuration/         ← Setup & config (examples, templates)
└── user-guides/           ← Practical guides (choosing models, running validations)
```

---

## State Tracking

**`project-state.json`** tracks:
- Current phase & progress
- Completed milestones
- Active decisions & blockers
- Notes & learnings
- Next steps

**🔄 Keep it updated!** Update after:
- Completing a phase
- Making key decisions
- Encountering blockers
- Learning something important

An AI assistant will remind you to update it.

---

## Common Tasks & What to Say

| What You Want | What to Say |
|---------------|-------------|
| Start coding | "Let's implement this" or "Start Phase 1" |
| Understand system | "Explain voice validation" or "Show architecture" |
| Choose model | "Which model?" or "Compare models" |
| Check costs | "How much?" or "Show pricing" |
| Configure | "How do I set this up?" or "Show config examples" |
| Get unstuck | "I'm blocked on X" (AI will update project-state.json) |

---

## Quick Reference Links

- 📊 **Current State**: [project-state.json](project-state.json)
- 📚 **Master Index**: [docs/INDEX.md](docs/INDEX.md)
- 🏗️ **Architecture**: [docs/rogue-integration/architecture.md](docs/rogue-integration/architecture.md)
- 📋 **Implementation**: [docs/implementation/README.md](docs/implementation/README.md)
- 🤖 **Model Selection**: [docs/user-guides/choosing-a-model.md](docs/user-guides/choosing-a-model.md)

---

**Last Updated**: 2026-01-11 | **Status**: Ready for implementation 🚀


