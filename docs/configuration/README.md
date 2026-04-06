# Configuration Guide

System configuration and model selection guidance for voice validation.

## Contents

- **[Model Selection](model-selection.md)**: How to choose the right model for your needs
- **[Validation Tiers](validation-tiers.md)**: FAST/FOCUSED/COMPREHENSIVE tier configuration
- **[LLM Config Examples](llm-config-examples.yaml)**: Configuration templates (YAML)
- **[Local vs Cloud](local-vs-cloud.md)**: Deployment options and trade-offs

## Quick Start

**Choose your configuration approach**:

1. **Quick setup** (use defaults):
```bash
# Uses recommended defaults (Sonnet for cloud, Qwen for local)
python -m waterrising validate-voice --chapter chapter_03.md
```

2. **Custom model**:
```bash
# Specify exact model
python -m waterrising validate-voice \
    --chapter chapter_03.md \
    --model claude-opus-4.5
```

3. **Validation tier**:
```bash
# Use pre-configured tier
python -m waterrising validate-voice \
    --chapter chapter_03.md \
    --tier COMPREHENSIVE
```

4. **Config file**:
```bash
# Load from config file
python -m waterrising validate-voice \
    --chapter chapter_03.md \
    --config my_config.yaml
```

## Configuration Hierarchy

Settings are loaded in this order (later overrides earlier):

1. **Default config** (built-in)
2. **Project config** (`waterrising.yaml` in project root)
3. **User config** (`~/.waterrising/config.yaml`)
4. **Environment variables** (`WATERRISING_MODEL`, etc.)
5. **Command-line arguments** (`--model`, `--tier`, etc.)

## Model Selection

See [Model Selection](model-selection.md) for detailed guide.

**Decision criteria**:
- **Budget**: Free (Tier 1) vs paid (Tier 2/3)
- **Accuracy**: How critical is catching subtle issues?
- **Speed**: How fast do you need results?
- **Privacy**: Can your text leave your machine?
- **Volume**: How many validations per month?

**Recommendations by use case**:

**Development/Iteration**:
```yaml
model: "qwen2.5-72b-ollama"
# Fast, free, good enough for drafts
```

**Production/Quality Checks**:
```yaml
model: "claude-sonnet-4.5"
# Balanced accuracy and cost
```

**Final Review/Critical Chapters**:
```yaml
model: "claude-opus-4.5"
# Highest accuracy when it matters
```

## Validation Tiers

See [Validation Tiers](validation-tiers.md) for detailed configuration.

Pre-configured validation profiles optimized for different scenarios:

**FAST**
- Model: Qwen 2.5 (72B) via Ollama
- Use case: Quick checks during writing
- Speed: <1 second
- Cost: $0.00
- Accuracy: Good for obvious violations

**FOCUSED**
- Model: Claude Sonnet 4.5
- Use case: Production validations
- Speed: 2-3 seconds
- Cost: ~$0.012
- Accuracy: Catches most issues

**COMPREHENSIVE**
- Model: Claude Opus 4.5
- Use case: Final review, critical validation
- Speed: 4-5 seconds
- Cost: ~$0.060
- Accuracy: Highest, catches subtle nuances

**Usage**:
```bash
python -m waterrising validate-voice \
    --chapter chapter_03.md \
    --tier COMPREHENSIVE
```

## Configuration File Format

See [LLM Config Examples](llm-config-examples.yaml) for templates.

**Basic config** (`waterrising.yaml`):
```yaml
# Model configuration
default_model: "claude-sonnet-4.5"
fallback_model: "qwen2.5-72b-ollama"

# API keys (or use environment variables)
anthropic_api_key: "${ANTHROPIC_API_KEY}"

# Validation settings
timeout_seconds: 60
max_retries: 3

# Cost tracking
cost_tracking:
  enabled: true
  alert_threshold: 10.00
```

**Tiered validation config**:
```yaml
validation_tiers:
  fast:
    model: "qwen2.5-72b-ollama"
    timeout_seconds: 30

  focused:
    model: "claude-sonnet-4.5"
    timeout_seconds: 60

  comprehensive:
    model: "claude-opus-4.5"
    timeout_seconds: 120
    max_output_tokens: 500
```

**Multi-provider config**:
```yaml
llm_providers:
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "https://api.anthropic.com"
    default_model: "claude-sonnet-4.5"

  ollama:
    base_url: "http://localhost:11434"
    default_model: "qwen2.5:72b"

  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4-turbo"
```

## Local vs Cloud Deployment

See [Local vs Cloud](local-vs-cloud.md) for detailed comparison.

**Local deployment** (Ollama):
- **Pros**: Free, fast, private, offline capable
- **Cons**: Lower accuracy, requires local resources
- **Best for**: Development, privacy-sensitive work

**Cloud deployment** (Claude, GPT):
- **Pros**: Highest accuracy, no local resources needed
- **Cons**: Costs money, requires internet, data leaves machine
- **Best for**: Production, quality-critical work

**Hybrid approach** (recommended):
```yaml
# Use local for development, cloud for production
development:
  model: "qwen2.5-72b-ollama"

production:
  model: "claude-sonnet-4.5"
  fallback_model: "qwen2.5-72b-ollama"  # If API fails
```

## Environment Variables

Override config with environment variables:

```bash
# Model selection
export WATERRISING_MODEL="claude-opus-4.5"

# API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# Ollama connection
export OLLAMA_BASE_URL="http://localhost:11434"

# Cost tracking
export WATERRISING_COST_TRACKING_ENABLED="true"
export WATERRISING_COST_ALERT_THRESHOLD="10.00"

# Validation settings
export WATERRISING_TIMEOUT="60"
export WATERRISING_MAX_RETRIES="3"
```

## Advanced Configuration

**Caching**:
```yaml
caching:
  enabled: true
  ttl_seconds: 3600
  cache_dir: ".waterrising/cache"
```

**Parallel processing**:
```yaml
parallel:
  enabled: true
  max_workers: 5
  max_concurrent_api_requests: 3
```

**Custom prompts**:
```yaml
prompts:
  voice_validation: |
    You are a voice consistency validator for character {character_name} at {arc_stage}.

    Character voice profile:
    {character_profile}

    Validate this excerpt:
    {excerpt}
```

**Logging**:
```yaml
logging:
  level: "INFO"
  file: "logs/waterrising.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Integration Points

- **Model Details** → See [Model Matrix](../model-testing/model-matrix.md)
- **Cost Planning** → See [Cost Analysis](../cost-analysis/README.md)
- **Architecture** → See [Architecture](../rogue-integration/architecture.md)
- **User Guide** → See [Running Validations](../user-guides/running-validations.md)

## Configuration Validation

Validate your config file:
```bash
python -m waterrising validate-config --config waterrising.yaml
```

Common issues:
- Invalid model names → See [Model Matrix](../model-testing/model-matrix.md)
- Missing API keys → Check environment variables
- Invalid YAML syntax → Use yamllint
- Port conflicts → Check Ollama is running on specified port

## Related Documentation

- **Model Selection** → [model-selection.md](model-selection.md)
- **Validation Tiers** → [validation-tiers.md](validation-tiers.md)
- **Config Templates** → [llm-config-examples.yaml](llm-config-examples.yaml)
- **Deployment** → [local-vs-cloud.md](local-vs-cloud.md)
- **User Guide** → [Running Validations](../user-guides/running-validations.md)
