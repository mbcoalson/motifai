# Interpreting Reports

Guide to understanding voice validation output and taking action.

## Report Structure

Voice validation reports contain:

1. **Header**: Character, arc stage, model used
2. **Flagged Passages**: Problematic text sections
3. **Explanations**: Why each passage is flagged
4. **Suggestions**: How to revise
5. **Summary**: Overall assessment

## Understanding Severity Levels

**Critical** (❌)
- Major voice inconsistency
- Character sounds completely wrong
- Action required before publication

Example: Blue-collar mechanic using academic jargon

**Moderate** (⚠️)
- Noticeable drift from character voice
- May break immersion for readers
- Should address in revision

Example: Gradual formalization of casual speech

**Info** (ℹ️)
- Minor potential issue
- May be intentional (edge case)
- Review but may be acceptable

Example: Single elevated word in informal passage

## Sample Report Walkthrough

```
VOICE VALIDATION REPORT
=======================
Character: Santiago Esposito
Arc Stage: Stage 1 (Blue-collar mechanic)
Model: claude-sonnet-4.5
Validation Date: 2026-01-11

FLAGGED PASSAGES
================

❌ CRITICAL: Line 23-24
"The algorithm of the tide is optimizing its flow patterns,"
Santiago observed, adjusting his toolkit with practiced precision.

Issue Type: Wrong diction register
Severity: Critical
Keywords: ["algorithm", "optimizing"]

Explanation:
Stage 1 Santiago is a practical, blue-collar boat mechanic. Terms like
"algorithm" and "optimizing" are software/tech jargon inappropriate for
this character at this point in his arc. He would use hands-on, concrete
language to describe what he's observing.

Suggested Revision:
"Tide's pulling harder than usual," Santiago said, checking his tools
one more time.

---

⚠️ MODERATE: Line 47
He contemplated the peculiar phenomenon manifesting in the harbor.

Issue Type: Diction drift
Severity: Moderate
Keywords: ["contemplated", "peculiar phenomenon", "manifesting"]

Explanation:
While less egregious than "algorithm", this language is still too formal
for Santiago. "Contemplated", "peculiar phenomenon", and "manifesting"
suggest an academic register. Stage 1 Santiago would think in simpler,
more direct terms.

Suggested Revision:
He tried to make sense of what he'd seen in the harbor.

---

SUMMARY
=======
Flagged: 2 passages (1 critical, 1 moderate)
Passed: 18 passages
Overall: Voice needs revision for character consistency

Recommendation:
Review critical flags immediately. Moderate flags should be addressed
in next revision.
```

## How to Act on Reports

### Critical Flags

**Always address these**:
1. Read the flagged passage in context
2. Compare to suggested revision
3. Rewrite using character-appropriate voice
4. Re-run validation to confirm fix

### Moderate Flags

**Evaluate in context**:
1. Is the drift intentional (character growth)?
2. Is it consistent with arc stage?
3. Would readers notice?
4. If yes to #3, revise

### Info Flags

**Review but may accept**:
1. Check if it's an edge case (mimicry, sarcasm)
2. If intentional, add context clues
3. If unintentional, consider revising
4. Document decision for future reference

## Comparing Model Reports

When using `--compare-models`, you'll see side-by-side results:

```
MODEL COMPARISON
================

Passage: "The algorithm of the tide..."

Claude Opus 4.5:    ❌ CRITICAL (detailed explanation)
Claude Sonnet 4.5:  ❌ CRITICAL (good explanation)
Qwen 2.5 (72B):     ❌ CRITICAL (basic explanation)

Agreement: All models flagged
Confidence: High (unanimous)
Action: Definitely revise

---

Passage: "Santiago rolled his eyes. 'Oh yeah, the algorithm...'"

Claude Opus 4.5:    ✅ PASS (recognized mimicry)
Claude Sonnet 4.5:  ✅ PASS (recognized context)
Qwen 2.5 (72B):     ❌ FLAG (missed context)

Agreement: Split (2/3 pass)
Confidence: Medium
Action: Likely valid edge case, Qwen missed context
```

**Interpretation**:
- **Unanimous flags**: Definitely revise
- **Unanimous pass**: Likely fine
- **Split decision**: Use your judgment, consider context

See [Model Comparison Results](model-comparison-results.md) for benchmark data.

## Common False Positives

**Intentional Code-Switching**:
- Character mimicking someone else
- Sarcasm/mockery using exaggerated language
- Quoting another character

**Fix**: Add context clues ("he said mockingly", quotation marks)

**Character Growth**:
- Vocabulary expanding as character evolves
- Appropriate for later arc stages

**Fix**: Verify it matches current arc stage, not premature

**Technical Dialogue**:
- Character explaining something they learned
- In-scene justification for technical language

**Fix**: Show the learning moment, make it earned

## Trusting Your Judgment

**Models are tools, not arbiters**:
- You know your character best
- Context matters more than individual words
- Some violations may be intentional

**When to override model**:
- Clear narrative reason for language choice
- Arc progression justifies vocabulary shift
- Intentional code-switching for effect

**When to trust model**:
- Multiple models agree
- You're unsure about character voice
- Early in writing process, patterns unclear

## Related Documentation

- **Model Selection** → [Choosing a Model](choosing-a-model.md)
- **Running Validations** → [Running Validations](running-validations.md)
- **Benchmark Results** → [Model Comparison Results](model-comparison-results.md)
- **Use Cases** → [Voice Validation Use Cases](../rogue-integration/use-cases.md)
