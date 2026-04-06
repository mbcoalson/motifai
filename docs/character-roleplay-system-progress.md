# Character Roleplay System - Development Log

**Project Goal:** Create a character consciousness simulator for Water Rising characters, allowing authentic roleplay interactions for testing narrative scenarios.

**Inspiration:** Stanford study where AI recreated real person's persona so accurately family couldn't distinguish on phone calls after 2-hour conversation.

**Status:** Phase 1 Complete - Foundation Built

---

## What We Built (Session: 2024-12-28)

### 1. Character Consciousness Builder (`build_character_consciousness.py`)

**Purpose:** Assembles complete character state from multiple source folders into dense, LLM-optimized format.

**Data Sources:**
- `Characters/` - Voice profiles, gestalt files, character essence
- `chapters/` - Lived experience chronologically (POV chapters only)
- `Continuity_Tracking/` - Physical state, relationships, knowledge bounds (partially implemented)

**Output:**
- JSON for LLM (structured character consciousness)
- Markdown for human review/tuning
- Cached for fast reuse in roleplay sessions

**Key Features:**
- Extracts core traits, dialogue samples, contradictions from voice profiles
- Parses gestalt files for physical presence, emotional signatures
- Assembles lived experience from chapter frontmatter + content
- Synthesizes current emotional state from recent chapters
- Caching system for performance

**Usage:**
```bash
python scripts/build_character_consciousness.py \
  --character "Santiago Esposito" \
  --date "2042-09-05" \
  --output-json .cache/santiago_consciousness.json \
  --output-md santiago_state.md
```

### 2. Minimal Prompt Methodology

**Key Insight:** Don't make LLM "perform" character traits. Make it BE the character.

**Approach:**
```
You ARE Santiago Esposito.

[Situational grounding: where, when, what just happened]

Below is data about your life and experiences. This is YOUR memory,
not a script. Reference it when relevant, but respond naturally.

Don't perform traits. Don't announce patterns. Just be.

[CONSCIOUSNESS DATA]

Don't overplay it.
```

**Tested with Santiago:**
- First test: Too performative ("look at me doing character traits!")
- Second test with minimal prompt: More natural, less self-conscious
- Still issues: Feels like "overzealous actor," voice affectations too strong

---

## What Works

✅ **Data extraction from existing character files** - Voice profiles, gestalt files parsed successfully
✅ **Chapter-based lived experience** - POV chapters provide grounding
✅ **Caching system** - Fast reloads for iterative testing
✅ **Minimal prompt reduces performance** - Characters feel more natural when not told to "act"
✅ **Foundation is solid** - Can extend to other characters (Anais, Joseph, etc.)

---

## Known Issues & Next Steps

### Issue 1: Santiago Feels "Overplayed"

**Symptoms:**
- Knows more than he feels
- Speech affectations too strong
- Voice doesn't capture Naples, FL regional blend:
  - Genteel northern influences
  - Miami proximity
  - Florida Cracker culture intersection
  - Working-class vernacular

**Root Cause:** Character documentation may be over-stylized, or LLM needs finer control

**Potential Solutions:**
1. **Trait Intensity Sliders (0-100 scores)**
   - Instead of: "Plain speech, economy of words"
   - Use: `plain_speech: 70, economy_of_words: 85, regional_vernacular: 45`
   - Allows fine-tuning without overcontrolling LLM

2. **Stanford Study Approach - Emergent Learning**
   - Multiple 2-hour roleplay sessions
   - Character "learns" from corrections during conversation
   - Build persona through interaction, not pre-programmed traits
   - Iterative refinement based on "does this feel right?" feedback

3. **Regional Voice Anchoring**
   - Collect actual Naples/SW Florida speech samples
   - Document cracker vernacular patterns
   - Capture Miami influence (Cuban-American proximity)
   - Add to dialogue samples with context weights

4. **Contradiction Balancing**
   - Current: Lists contradictions as text
   - Better: Weight opposing tendencies (patience: 80, impatience_under_stress: 60)
   - Let LLM navigate tension naturally

### Issue 2: Missing Data Components

**Not Yet Implemented:**
- Knowledge bounds extraction (what character knows/doesn't know)
- Relationship state parsing from Continuity_Tracking
- Physical state from health/possession logs
- Sensory filter extraction from profiles (touch>sound>sight)
- Voice stage auto-detection from chapter range

**Impact:** Character has shallow context, limited grounding

**Next Session Priority:** Complete these extractors

### Issue 3: No Standalone Conversation Tool

**Current State:** Testing via Claude Code conversations (manual)

**Need:** CLI tool for independent roleplay sessions
- `talk_to_character.py` with OpenAI/Anthropic API
- Session logging and resume capability
- Transcript export for analysis
- Multi-turn conversation memory

---

## Architecture Decisions (Locked)

1. **Consciousness data = memory reference, not performance script**
2. **Minimal prompting >> detailed instruction**
3. **Trust LLM to inhabit, don't force it to perform**
4. **Caching for fast iteration**
5. **Human-in-the-loop tuning after each test**

---

## Future Phases

### Phase 2: Refinement System
- Trait intensity sliders (0-100 weighting)
- Iterative tuning workflow
- Session-based learning (Stanford approach)
- Regional voice anchoring system

### Phase 3: Multi-Character System
- Test with Anais, Joseph
- Character-to-character interaction engine
- GM scenario mode (you set scene, characters respond)
- Relationship dynamics in real-time

### Phase 4: Extended Sessions
- 2+ hour conversations like Stanford study
- Character evolution tracking
- Consistency validation ("Turing test" - can readers tell?)
- Emergent persona refinement

---

## File Locations

**Tools:**
- `scripts/build_character_consciousness.py` - Character state builder
- `scripts/get_character_state.py` - Original chapter-based tool (superseded)

**Cache:**
- `.cache/character_consciousness/*.json` - Built character states
- `.cache/character_states/*.json` - Original tool cache

**Documentation:**
- `docs/character-roleplay-system-progress.md` - This file
- `docs/claude-code-handoff.md` - Previous session notes
- `docs/tool-architecture.md` - CLI tool design principles

---

## Notes for Next Session

**User Feedback (2024-12-28):**
> "Santiago still feels like an overzealous actor who knows more than they feel. His speech affectations are too strong. There's a common lingo in the States, even if there are regional differences. Santiago's voice doesn't feel grounded in that Naples, FL strangeness of gentile northern influences, miami proximity, Florida Cracker intersection."

**Hypothesis:** Need trait intensity system (0-100 scores) for fine-tuning without overcontrolling LLM.

**Questions to Explore:**
1. Can we use Stanford study's iterative conversation method to BUILD the character voice instead of pre-defining it?
2. Should dialogue samples be weighted by context/situation?
3. How do we capture regional speech patterns without phonetic dialect spelling?
4. Is the issue in the source files (over-stylized writing) or the extraction/prompting?

**Action Items:**
1. Research Naples/SW Florida regional speech patterns
2. Design trait weighting system (0-100 scores)
3. Complete missing data extractors (knowledge bounds, relationships)
4. Test longer conversation sessions (30+ minutes)
5. Consider building voice through interaction rather than documentation

---

## Success Criteria

**Character feels "right" when:**
- Responses are natural, not performative
- Voice matches region/background organically
- Contradictions emerge naturally, not announced
- User can't tell it's an LLM after extended conversation
- Character surprises user with authentic responses
- No "I'm doing the character trait now" vibe

**We're not there yet with Santiago, but foundation is solid.**

---

**Last Updated:** 2024-12-28
**Session Duration:** ~4 hours
**Next Session Focus:** Trait weighting system + regional voice anchoring
