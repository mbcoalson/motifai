# Running Validations

Practical guide for running voice validations from the command line.

## Quick Start

Basic validation:
```bash
python -m waterrising validate-voice \
    --chapter chapters/chapter_03.md \
    --character "Santiago Esposito"
```

## Command Options

See [Configuration Guide](../configuration/README.md) for detailed options.

**Basic usage**:
- `--chapter`: Path to chapter file
- `--character`: Character name to validate
- `--model`: Specific model to use (default: claude-sonnet-4.5)
- `--tier`: Validation tier (FAST/FOCUSED/COMPREHENSIVE)

**Advanced options**:
- `--compare-models`: Compare multiple models
- `--config`: Load from config file
- `--output`: Save results to file

## Examples

**Quick check** (local model):
```bash
waterrising validate-voice --chapter ch03.md --tier FAST
```

**Production validation**:
```bash
waterrising validate-voice --chapter ch03.md --tier FOCUSED
```

**Final review**:
```bash
waterrising validate-voice --chapter ch03.md --tier COMPREHENSIVE
```

**Model comparison**:
```bash
waterrising validate-voice --chapter ch03.md \
    --compare-models qwen2.5-72b,claude-sonnet-4.5,claude-opus-4.5
```

## Output Format

Validation results include:
- **Flagged passages**: Specific text with voice issues
- **Severity**: Critical, moderate, or info
- **Explanation**: Why it's inconsistent
- **Suggestion**: How to fix it

Example output:
```
VOICE VALIDATION REPORT
Character: Santiago Esposito
Arc Stage: Stage 1
Model: claude-sonnet-4.5

❌ FLAGGED (Critical)
Line 23: "The algorithm of the tide is optimizing..."

Issue: Wrong diction register
Keywords: "algorithm", "optimizing"
Explanation: Tech jargon inappropriate for blue-collar mechanic at Stage 1

Suggestion:
"Tide's pulling harder than usual," Santiago said...
```

See [Interpreting Reports](interpreting-reports.md) for detailed guide.

## Batch Validation

Validate multiple chapters:
```bash
for chapter in chapters/*.md; do
  waterrising validate-voice --chapter "$chapter" --output "results/$(basename $chapter).json"
done
```

## Integration with Writing Workflow

**Draft stage**:
```bash
# Quick checks while writing
waterrising validate-voice --chapter draft/ch03.md --tier FAST
```

**Revision stage**:
```bash
# More thorough validation
waterrising validate-voice --chapter revision/ch03.md --tier FOCUSED
```

**Final stage**:
```bash
# Highest accuracy for final review
waterrising validate-voice --chapter final/ch03.md --tier COMPREHENSIVE
```

## Related Documentation

- **Model Selection** → [Choosing a Model](choosing-a-model.md)
- **Configuration** → [Configuration Guide](../configuration/README.md)
- **Interpreting Results** → [Interpreting Reports](interpreting-reports.md)
- **Use Cases** → [Voice Validation Use Cases](../rogue-integration/use-cases.md)
