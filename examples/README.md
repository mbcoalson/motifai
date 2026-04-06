# Voice Validation Examples

This directory contains example scripts demonstrating how to use the LLM adapters for character voice validation.

## Examples

### 1. Basic Validation (`basic_validation.py`)

Demonstrates the core validation workflow with a single character and two excerpts (one good, one bad).

**What it shows:**
- Loading character profiles from YAML
- Creating LLM adapters
- Running voice validation
- Interpreting validation results
- Generating reports

**Run with Ollama (free, local):**
```bash
# Make sure Ollama is running and model is pulled
ollama pull qwen2.5:72b

# Run example
python examples/basic_validation.py
```

**Run with Claude (requires API key):**
```bash
# Set API key
export ANTHROPIC_API_KEY=your-key-here

# Edit basic_validation.py and change:
# adapter = create_llm_adapter("qwen2.5-72b")
# to:
# adapter = create_llm_adapter("claude-sonnet-4.5")

# Run example
python examples/basic_validation.py
```

### 2. Provider Comparison (`compare_providers.py`)

Compares different LLM providers (Ollama vs Claude) on the same validation task.

**What it shows:**
- Testing multiple providers
- Performance comparison
- Cost vs quality tradeoffs
- Choosing the right model for your workflow

**Requirements:**
- Ollama running with qwen2.5:72b
- ANTHROPIC_API_KEY set

**Run:**
```bash
export ANTHROPIC_API_KEY=your-key-here
python examples/compare_providers.py
```

## Expected Output

### Basic Validation Example

```
============================================================
Voice Validation Example
============================================================

Step 1: Loading character profile...
✓ Loaded profile for: Santiago Esposito
  Role: Protagonist
  Traits: practical, blue-collar, skeptical

Step 2: Creating LLM adapter...
✓ Created ollama adapter
  Model: qwen2.5:72b

Step 3: Checking LLM availability...
✓ LLM is available and responding

Step 4: Validating GOOD excerpt (should pass)...
  Status: PASSED
  Confidence: 94.5%
  Severity: passed
  Summary: The excerpt matches Santiago's voice well...

Step 5: Validating BAD excerpt (should fail)...
  Status: FAILED
  Confidence: 89.2%
  Severity: critical

  Flagged Issues:
    1. [CRITICAL] Indubitably
       Reason: This word is in the character's forbidden vocabulary
       Suggestion: Use simpler language like 'definitely' or 'yeah'
```

## Tips

### For Development
- Use Ollama models (qwen2.5-72b, llama3.1-70b) - free and fast
- Perfect for iterative testing and development

### For Production
- Use Claude Sonnet 4.5 for balanced cost/quality
- Use Claude Opus 4.5 for highest quality on critical chapters

### Switching Providers

The factory pattern makes it easy to switch:

```python
# Local/Free
adapter = create_llm_adapter("qwen2.5-72b")

# Cloud/Paid
adapter = create_llm_adapter("claude-sonnet-4.5")

# All use the same interface!
result = adapter.validate_voice(profile, excerpt, chapter=1)
```

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Pull the model: `ollama pull qwen2.5:72b`

### "Claude requires an API key"
- Set environment variable: `export ANTHROPIC_API_KEY=your-key`
- Or pass directly: `create_llm_adapter("claude-sonnet-4.5", api_key="your-key")`

### "Health check failed"
- For Ollama: Ensure the model is pulled and server is running
- For Claude: Verify API key is valid

## Next Steps

After running these examples, you can:

1. Create your own character profiles in `config/stories/your_story/characters/`
2. Validate your own text excerpts
3. Integrate validation into your writing workflow
4. Build custom tools on top of the adapters

See the main documentation for more advanced usage patterns.
