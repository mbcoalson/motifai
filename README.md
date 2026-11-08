# Motifai

**A work-in-progress voice-validation tool for fiction writers.** Motifai compares prose with character voice profiles to help surface possible diction drift, register mismatches, and arc-stage inconsistencies before a reader finds them.

It is a creative aid, not an authority on a character, a substitute for an editor, or a machine that can tell writers what their stories ought to be.

## What it does today

Motifai combines:

- **Character voice profiles** in YAML: traits, speech patterns, arc stages, voice samples, and optional forbidden words
- **Deterministic pre-checks** for explicit constraints such as forbidden vocabulary and register mismatches
- **LLM-assisted review** for subtler voice questions, using either a local Ollama model or Claude
- **Structured results** that retain individual flags, reasons, severity, and suggestions

The core uses a ports-and-adapters design, keeping character models and validation logic separate from individual LLM providers.

## Status

The domain models, validation services, Claude adapter, Ollama adapter, examples, and unit tests are present. Motifai remains under active development: its command-line packaging, configuration experience, and benchmark suite are not yet a stable general-release interface.

Treat model feedback as a prompt for human review. Model output can be wrong, overly literal, or blind to context that matters to the author.

## Quick start for contributors

Motifai currently targets Python 3.10 or newer.

```bash
git clone https://github.com/mbcoalson/motifai.git
cd motifai
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -e .
pytest tests/unit/ -q
```

The packaging and entry points are still being reconciled with the current project structure. The examples in [`examples/`](examples/) are the clearest starting point for exercising the present validation flow.

## Privacy and model choice

Character profiles and excerpts are creative work. Do not send material to a cloud model unless you are comfortable with that provider’s terms and your own sharing rights. Local Ollama support exists for people who prefer to keep validation on their own machine, with the usual tradeoffs in model quality and hardware requirements.

The repository does not include private manuscripts or story data; examples should remain synthetic or explicitly shareable.

## Repository guide

- [`src/domain/`](src/domain/) — character and validation domain models
- [`src/adapters/llm/`](src/adapters/llm/) — Claude and Ollama integrations
- [`examples/`](examples/) — small, runnable demonstrations
- [`docs/`](docs/) — architecture, configuration, and user guidance
- [`tests/unit/`](tests/unit/) — unit tests

## Roadmap

Near-term work includes a coherent command-line interface, a clearer multi-story configuration path, stronger type coverage, and a benchmark suite that tests meaningful voice-validation cases rather than marketing claims.

## License

MIT — see [LICENSE](LICENSE).
