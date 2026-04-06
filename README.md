# motifai

**AI-powered voice validation for fiction writers.** Motifai checks your prose against character profiles to catch voice inconsistencies before your readers do.

Writers define character voice profiles (vocabulary, speech patterns, arc stages) in YAML. Motifai validates excerpts against those profiles using LLM analysis, flagging diction drift, register mismatches, and arc-stage violations. It supports local models (Ollama) and cloud models (Claude) so you can choose your own accuracy/cost/privacy tradeoff.

---

## What It Does

- **Voice consistency checking** -- Validates dialogue and narration against character voice profiles
- **Arc-stage awareness** -- Understands that characters evolve; flags language that's wrong *for where they are in the story*
- **Deterministic pre-checks** -- Catches forbidden words and register violations before calling the LLM, saving time and API cost
- **Multi-model support** -- Swap between local (Ollama/Qwen) and cloud (Claude Sonnet, Opus) providers with one config change
- **Story-agnostic design** -- Character profiles are YAML configs, not hardcoded. Bring your own characters

---

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) [Ollama](https://ollama.com) for free local inference
- (Optional) Anthropic API key for Claude models

### Install

```bash
git clone https://github.com/mbcoalson/motifai.git
cd motifai
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure

1. Copy `.env.example` to `.env` (if using Claude):
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

2. Create a character profile in `config/stories/your_story/characters/`:
   ```yaml
   name: Your Character
   role: protagonist
   basic_traits:
     - practical
     - working-class
     - skeptical
   arc_stages:
     - name: "Stage 1"
       description: "Before the inciting incident"
       vocabulary_register: informal
       forbidden_words:
         - algorithm
         - methodology
         - subsequently
   ```

### Run

```bash
# With Ollama (free, local):
python examples/basic_validation.py --provider ollama

# With Claude (requires API key):
python examples/basic_validation.py --provider claude
```

---

## How It Works

### Architecture

Motifai uses a **hexagonal (ports & adapters) architecture** so the core validation logic has zero dependencies on any specific LLM provider, file format, or interface:

```
Character Profile (YAML)
    |
    v
ValidationService (domain core)
    |
    +-- DeterministicValidator  -- forbidden words, register checks (instant, free)
    |
    +-- LLMAdapter (port)
            |
            +-- ClaudeAdapter   -- Anthropic API
            +-- OllamaAdapter   -- Local models via Ollama
```

### Validation Flow

1. **Load character profile** from YAML config (name, traits, arc stages, voice samples, forbidden words)
2. **Deterministic pre-check** catches hard violations (forbidden vocabulary, register mismatches) without an LLM call
3. **LLM validation** sends the excerpt + profile + arc stage context to the model for deeper voice analysis
4. **Merge results** -- deterministic and LLM findings are deduplicated into a single report with severity levels and suggestions

### Domain Models

| Model | Purpose |
|-------|---------|
| `CharacterProfile` | Voice profile with traits, arc stages, samples, forbidden words |
| `ArcStage` | Stage of character development with stage-specific voice rules |
| `VoiceSample` | Example dialogue demonstrating correct voice |
| `ValidationResult` | Structured output with flags, severity, confidence, suggestions |
| `FlaggedPassage` | Individual voice violation with reason and suggested fix |

---

## Project Structure

```
motifai/
  config/
    tool_registry.yaml       # Tool definitions for LLM agent integration
    stories/                  # Character profiles per story (gitignored)
  configs/
    settings.yaml             # Application settings
  docs/
    ARCHITECTURE.md           # System architecture
    chapter-frontmatter-schema.md
    tool-architecture.md      # CLI tool interface contract
    configuration/            # LLM and validation tier config guides
    user-guides/              # How to run validations, interpret reports, choose models
  examples/
    basic_validation.py       # End-to-end voice validation demo
    compare_providers.py      # Multi-model comparison demo
  scripts/
    validate_chapters.py      # Chapter frontmatter validation
    query_chapters.py         # Chapter metadata queries
    get_character_state.py    # Character state at a story point
    build_character_consciousness.py  # Full character grounding
    migrate_chapters.py       # Batch frontmatter migration
    update_word_counts.py     # Accurate word count updates
    verify_models.py          # LLM provider health checks
    demo_validate.py          # Demo validation pipeline
  src/
    domain/
      models/                 # CharacterProfile, ArcStage, ValidationResult, etc.
      services/               # ValidationService, DeterministicValidator
    adapters/
      llm/                    # ClaudeAdapter, OllamaAdapter, LLMFactory
    ports/                    # LLMAdapter interface (abstract)
    schemas/                  # Chapter schema definitions
  tests/
    unit/                     # Pytest suite (domain models, adapters, services)
```

---

## Validation Tiers

Choose the right model for the job:

| Tier | Model | Cost | Speed | Best For |
|------|-------|------|-------|----------|
| **FAST** | Qwen 2.5 (72B) via Ollama | Free | ~0.8s | Drafting, frequent checks |
| **FOCUSED** | Claude Sonnet | ~$0.01/check | ~2.3s | Production editing |
| **COMPREHENSIVE** | Claude Opus | ~$0.06/check | ~4.1s | Final passes, critical chapters |

---

## Roadmap

Motifai is under active development. Here's what's built and what's coming:

### Implemented

- [x] Hexagonal architecture (domain / ports / adapters)
- [x] Character profile system (YAML-based, story-agnostic, arc-stage aware)
- [x] Deterministic validator (forbidden words, register checks)
- [x] LLM validation via Claude adapter (Anthropic API)
- [x] LLM validation via Ollama adapter (local models)
- [x] LLM factory for provider switching
- [x] ValidationService orchestrator (deterministic + LLM merge)
- [x] Chapter metadata tools (validate, query, migrate, word counts)
- [x] Character state grounding (build knowledge at a story point)
- [x] Unit test suite (domain models, adapters, services)
- [x] Examples (basic validation, provider comparison)

### In Progress

- [ ] **CLI interface** -- `motifai validate-voice --chapter ch03.md --character "Your Character"` command-line workflow
- [ ] **Story configuration system** -- Full multi-story support via `config/stories/` with startup validation
- [ ] **Type safety pass** -- `mypy --strict` across all public APIs

### Planned

- [ ] **Model comparison framework** -- Run the same excerpt against multiple models in parallel, get a side-by-side accuracy/speed/cost report
- [ ] **Benchmark suite** -- Standardized scenarios (clear violations, subtle drift, arc mismatches, valid edge cases) scored across models
- [ ] **Self-improving profiles** -- Integration with [claude-reflect-system](https://github.com/haddock-development/claude-reflect-system) so character profiles learn from your corrections automatically
- [ ] **n8n workflow automation** -- Scheduled validation runs, index rebuilds, and notifications via n8n
- [ ] **Incremental FAISS updates** -- Append new chapters to the semantic index without full rebuilds
- [ ] **Batch validation** -- Validate an entire act or manuscript in one pass
- [ ] **IDE integration** -- VS Code extension for inline voice validation feedback

### Future

- [ ] OpenAI adapter (GPT-4 Turbo, GPT-4o)
- [ ] REST API for SaaS deployment
- [ ] Multi-language support
- [ ] Web UI

---

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -q

# With coverage
pytest tests/unit/ --cov=src

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

---

## Configuration

### LLM Providers

Configure in `configs/settings.yaml` or via environment variables:

```yaml
llm_providers:
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: "claude-sonnet-4-20250514"
  ollama:
    base_url: "http://localhost:11434"
    default_model: "qwen2.5:72b"
```

### Character Profiles

Profiles live in `config/stories/{story_name}/characters/{character}.yaml`. At minimum, a profile needs a `name`. Everything else is optional -- the more you provide, the better the validation:

- `basic_traits` -- personality descriptors
- `arc_stages` -- voice evolution through the story
- `voice_samples` -- example dialogue showing correct voice
- `forbidden_words` -- words the character would never use (per arc stage)
- `sensory_filter` -- which senses the character notices most
- `contradictions` -- internal conflicts that inform voice

See [docs/chapter-frontmatter-schema.md](docs/chapter-frontmatter-schema.md) for the full schema.

---

## Tool Registry

Motifai includes a registry of CLI tools designed for LLM agent integration. Each tool:
- Accepts arguments via `argparse`
- Returns structured JSON to stdout
- Supports dry-run mode for mutation operations

See [docs/tool-architecture.md](docs/tool-architecture.md) for the interface contract and [config/tool_registry.yaml](config/tool_registry.yaml) for the full tool list.

---

## Contributing

Motifai is in early development. Contributions welcome -- especially:

- New LLM adapters (OpenAI, Llama.cpp, etc.)
- Character profile templates for different genres
- Benchmark scenarios
- Documentation improvements

Please open an issue before starting work on large changes.

---

## License

See [LICENSE](LICENSE) for details.
