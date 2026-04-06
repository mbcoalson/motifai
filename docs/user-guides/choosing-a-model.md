# Choosing a Model

Decision guide for selecting the right LLM model for your voice validation needs.

## Quick Decision Tree

```
What's your top priority?

├─ Cost = Zero
│  └─ Use: Qwen 2.5 (72B) via Ollama
│     - Free, fast, good for drafts
│     - See: Local Setup section below
│
├─ Privacy = Critical (data cannot leave machine)
│  └─ Use: Local models only (Tier 1)
│     - Qwen 2.5 or Llama 3.1 via Ollama
│     - See: Privacy-First Configuration
│
├─ Accuracy = Highest priority
│  └─ Use: Claude Opus 4.5
│     - Best performance on subtle voice issues
│     - ~$0.060 per validation
│     - See: Quality-First Configuration
│
└─ Balanced (typical use case)
   ├─ Frequent validations (>100/month)
   │  └─ Use: Qwen for drafts + Sonnet for finals
   │     - $1-2/month budget
   │     - See: Cost-Optimized Workflow
   │
   └─ Occasional validations (<100/month)
      └─ Use: Claude Sonnet 4.5
         - ~$1.20/month (100 validations)
         - See: Standard Configuration
```

## Decision Factors

### 1. Budget

**Zero Budget**:
- **Recommended**: Qwen 2.5 (72B) via Ollama
- **Why**: Completely free after initial download
- **Trade-off**: Lower accuracy (~78% F1 vs 95% for Opus)
- **Best for**: Students, hobbyists, high-volume draft checking

**Small Budget ($1-5/month)**:
- **Recommended**: Claude Sonnet 4.5 for important validations
- **Strategy**: Use Qwen for drafts, Sonnet for revisions
- **Example**: 100 Sonnet validations = $1.20/month
- **Best for**: Indie authors, occasional use

**Moderate Budget ($5-20/month)**:
- **Recommended**: Sonnet as primary, Opus for critical chapters
- **Strategy**: Tiered validation (Qwen → Sonnet → Opus)
- **Example**: 200 Sonnet + 50 Opus = $7.40/month
- **Best for**: Active authors, quality-focused

**Unlimited Budget**:
- **Recommended**: Claude Opus 4.5 for everything
- **Why**: Highest accuracy, best explanations
- **Cost**: ~$30/month for 500 validations
- **Best for**: Professional authors, publishing houses

### 2. Accuracy Requirements

**Draft Stage** (catching obvious errors):
- **Sufficient**: Qwen 2.5 (F1: ~0.78)
- **Good at**: Clear voice violations, wrong diction
- **Misses**: Subtle tone shifts, edge cases
- **Recommendation**: Tier 1 models fine here

**Revision Stage** (catching most errors):
- **Recommended**: Claude Sonnet 4.5 (F1: ~0.89)
- **Good at**: Most voice issues, diction drift
- **Misses**: Some edge cases (intentional code-switching)
- **Recommendation**: Tier 2 models

**Final Review** (catching everything):
- **Required**: Claude Opus 4.5 (F1: ~0.95)
- **Good at**: All scenarios including subtle nuances
- **Catches**: Edge cases, emotional tone issues
- **Recommendation**: Tier 3 models only

### 3. Speed Requirements

**Real-time feedback** (writing flow):
- **Fastest**: Qwen 2.5 (~0.8s latency)
- **Use case**: Check as you write
- **Trade-off**: Lower accuracy for speed

**Standard workflow** (periodic checks):
- **Balanced**: Claude Sonnet (~2.3s latency)
- **Use case**: Validate after completing scenes
- **Sweet spot**: Good speed + accuracy

**Deep analysis** (no rush):
- **Highest quality**: Claude Opus (~4.1s latency)
- **Use case**: Final chapter review
- **Trade-off**: Wait longer for best results

### 4. Privacy Concerns

**Data can leave machine**:
- **Options**: Any model (Tier 1, 2, or 3)
- **Recommended**: Based on budget/accuracy needs

**Data cannot leave machine**:
- **Required**: Local models only
- **Options**: Qwen 2.5 or Llama 3.1 via Ollama
- **Trade-off**: Lower accuracy for complete privacy
- **Configuration**: See Privacy-First section

### 5. Usage Volume

**Low volume** (<20 validations/month):
- **Recommended**: Claude Sonnet 4.5
- **Cost**: ~$0.24/month
- **Why**: Cost negligible, get good accuracy

**Medium volume** (20-100 validations/month):
- **Recommended**: Tiered approach
  - Drafts: Qwen (free)
  - Finals: Sonnet ($1-2/month)
- **Why**: Optimize cost without sacrificing quality

**High volume** (100+ validations/month):
- **Recommended**: Primarily Qwen, Sonnet for finals
- **Cost**: $1-5/month (mostly Sonnet cost)
- **Why**: Qwen handles bulk, Sonnet for critical checks

**Very high volume** (500+ validations/month):
- **Recommended**: Custom workflow
  - Quick checks: Qwen
  - Standard: Sonnet
  - Critical: Opus
- **Cost**: $10-30/month
- **Why**: Need automation and smart routing

## Recommended Configurations

### Standard Configuration (Most Users)

**Profile**: Active author, 50-100 validations/month, balanced priorities

**Model**: Claude Sonnet 4.5
**Monthly cost**: ~$1.20
**Setup**:
```yaml
default_model: "claude-sonnet-4.5"
fallback_model: "qwen2.5-72b-ollama"
```

**When to use**:
- Writing regular chapters
- Second draft review
- Quality checks before sharing

---

### Cost-Optimized Workflow

**Profile**: Frequent validations, minimal budget

**Models**:
- Draft: Qwen 2.5 (free)
- Revision: Claude Sonnet 4.5
- Final: Claude Opus 4.5 (critical chapters only)

**Monthly cost**: $2-5 (depends on Sonnet/Opus ratio)

**Setup**:
```yaml
validation_tiers:
  draft: "qwen2.5-72b-ollama"
  revision: "claude-sonnet-4.5"
  final: "claude-opus-4.5"
```

**Workflow**:
```bash
# Draft validation (free, fast)
waterrising validate-voice --chapter ch03_draft.md --tier draft

# Revision validation (balanced)
waterrising validate-voice --chapter ch03_v2.md --tier revision

# Final validation (highest accuracy)
waterrising validate-voice --chapter ch03_final.md --tier final
```

---

### Quality-First Configuration

**Profile**: Professional author, quality critical, budget flexible

**Model**: Claude Opus 4.5 for everything
**Monthly cost**: $30-60 (500-1000 validations)

**Setup**:
```yaml
default_model: "claude-opus-4.5"
max_output_tokens: 1000  # Detailed explanations
```

**When to use**:
- Publishing house quality standards
- Critical character voice precision
- Every validation matters

---

### Privacy-First Configuration

**Profile**: Confidential manuscript, data cannot leave machine

**Model**: Qwen 2.5 (72B) via Ollama
**Monthly cost**: $0.00

**Setup**:
```yaml
model: "qwen2.5-72b-ollama"
cloud_providers_enabled: false
offline_mode: true
```

**Trade-offs**:
- Lower accuracy (F1: 0.78 vs 0.95)
- May miss subtle issues
- Requires local GPU or CPU (slower)

**Mitigation**:
- Run multiple local models and compare
- Use stricter character profiles
- Manual review for edge cases

---

### Development Configuration

**Profile**: Testing, frequent iterations, not production

**Model**: Qwen 2.5 (local)
**Monthly cost**: $0.00

**Setup**:
```yaml
model: "qwen2.5-72b-ollama"
caching:
  enabled: true
  ttl_seconds: 3600
logging:
  level: "DEBUG"
```

**Why**: Free, fast feedback loop, good enough for development

## Model Comparison Table

| Model | Tier | F1 Score | Latency | Cost | Best For |
|-------|------|----------|---------|------|----------|
| Qwen 2.5 (72B) | 1 | 0.78 | 0.8s | $0.00 | Development, drafts, privacy |
| Llama 3.1 (70B) | 1 | 0.76 | 1.2s | $0.00 | Alternative local option |
| Claude Sonnet 4.5 ⭐ | 2 | 0.89 | 2.3s | $0.012 | **Most users** (balanced) |
| GPT-4 Turbo | 2 | 0.85 | 2.8s | $0.013 | OpenAI ecosystem users |
| Claude Opus 4.5 | 3 | 0.95 | 4.1s | $0.060 | Final review, critical work |
| GPT-4o | 3 | 0.88 | 2.5s | $0.050 | Alternative premium option |

⭐ = Recommended for most users

See [Model Matrix](../model-testing/model-matrix.md) for detailed specs.

## FAQ

**Q: Can I switch models mid-project?**
A: Yes! You can change models anytime. Validations are independent.

**Q: Will different models give different results?**
A: Yes. Tier 3 models catch more subtle issues. See [Benchmark Results](model-comparison-results.md).

**Q: Can I use multiple models for the same chapter?**
A: Yes! Use `--compare-models` flag:
```bash
waterrising validate-voice --chapter test.md \
  --compare-models qwen2.5-72b,claude-sonnet-4.5,claude-opus-4.5
```

**Q: What if Ollama isn't working?**
A: Cloud models work without Ollama. Or troubleshoot: [Local vs Cloud](../configuration/local-vs-cloud.md)

**Q: Can I fine-tune a model for my characters?**
A: Not yet. Planned for future releases. Currently relies on prompt engineering.

**Q: Which model for non-English text?**
A: Claude Opus best for multilingual. Qwen also has good multilingual support.

## Next Steps

1. **Choose your model** based on decision tree above
2. **Set up configuration**: See [Configuration Guide](../configuration/README.md)
3. **Run your first validation**: See [Running Validations](running-validations.md)
4. **Compare models** (optional): See [Model Comparison](model-comparison-results.md)

## Related Documentation

- **Model Details** → [Model Matrix](../model-testing/model-matrix.md)
- **Cost Analysis** → [Cost Analysis](../cost-analysis/README.md)
- **Configuration** → [Configuration Guide](../configuration/README.md)
- **Benchmark Results** → [Model Comparison Results](model-comparison-results.md)
