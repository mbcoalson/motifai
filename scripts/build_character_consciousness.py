#!/usr/bin/env python3
"""
build_character_consciousness.py - Assembles complete character consciousness

This is the Phase 1 foundation tool. It reads ALL character sources:
- Characters/* (voice profiles, gestalt, essence)
- chapters/* (lived experience chronologically)
- Continuity_Tracking/* (physical state, relationships, knowledge bounds)

And outputs a DENSE, LLM-optimized character state that allows the LLM to
**BE** the character, not just "roleplay" them.

Output:
  - JSON for LLM (structured, dense, ready to internalize)
  - Markdown for human (readable summary for tuning)
"""

import argparse
import json
import re
import sys
import yaml
from pathlib import Path
from datetime import date
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from schemas.chapter_schema import CANONICAL_CHARACTERS


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class CharacterConsciousness:
    """
    Complete character consciousness at a moment in time.
    This is what the LLM internalizes to BE the character.
    """
    # Identity
    name: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)

    # Temporal grounding
    as_of_date: str = ""
    as_of_chapter: int = 0

    # Core essence (never changes)
    core_identity: str = ""  # Who they fundamentally are
    core_traits: List[str] = field(default_factory=list)
    fatal_flaw: str = ""
    contradictions: List[str] = field(default_factory=list)

    # Voice & Expression
    voice_cadence: str = ""  # How they speak
    physical_presence: str = ""  # How they move/exist in space
    sensory_filter: str = ""  # How they perceive (touch>sound>sight, etc.)
    dialogue_samples: List[str] = field(default_factory=list)

    # Emotional Architecture
    emotional_state_now: str = ""  # Current emotional condition
    emotional_chords: Dict[str, str] = field(default_factory=dict)  # Complex emotional combinations

    # Lived Experience (chronological)
    chapters_lived: List[Dict[str, Any]] = field(default_factory=list)
    key_moments: List[str] = field(default_factory=list)  # Pivotal experiences

    # Knowledge & Beliefs
    knows: List[str] = field(default_factory=list)
    does_not_know: List[str] = field(default_factory=list)
    believes_incorrectly: List[str] = field(default_factory=list)

    # Relationships
    relationships: Dict[str, str] = field(default_factory=dict)  # {character: relationship_state}

    # Physical State
    location: str = ""
    physical_condition: str = ""
    possessions: List[str] = field(default_factory=list)

    # Current Drivers
    immediate_need: str = ""  # What they want/need RIGHT NOW
    current_goal: str = ""  # What they're working toward

    # Meta (for LLM guidance)
    voice_stage: str = ""  # Which arc stage they're in
    how_to_sound: str = ""  # Direct instruction for voice


# =============================================================================
# Source Parsers
# =============================================================================

class CharacterSourceParser:
    """Parse character files to extract essence"""

    def __init__(self, characters_dir: Path):
        self.characters_dir = characters_dir

    def find_files(self, character_name: str) -> Dict[str, Path]:
        """Find all files related to this character"""
        files = {}
        if not self.characters_dir.exists():
            return files

        # Normalize character name for matching
        first_name = character_name.split()[0].lower()

        for file_path in self.characters_dir.rglob("*.md"):
            filename = file_path.stem.lower()

            if first_name in filename:
                if "voice" in filename and "profile" in filename:
                    files["voice_profile"] = file_path
                elif "gestalt" in filename:
                    files["gestalt"] = file_path
                elif "instruction" in filename:
                    files["instructions"] = file_path
                elif "knowledge" in filename:
                    files["knowledge_bounds"] = file_path

        return files

    def parse_voice_profile(self, file_path: Path) -> Dict[str, Any]:
        """Extract structured data from voice profile"""
        if not file_path.exists():
            return {}

        content = file_path.read_text(encoding='utf-8')
        result = {}

        # Core traits (CONSTANTS section)
        constants_section = re.search(
            r'### \*\*CONSTANTS \(Never Change\):\*\*(.*?)(?=###|\Z)',
            content, re.DOTALL
        )
        if constants_section:
            traits = re.findall(
                r'\d+\.\s+\*\*(.*?)\*\*\s+-\s+(.*?)(?=\n\d+\.|\n###|\Z)',
                constants_section.group(1), re.DOTALL
            )
            result["core_traits"] = [
                f"{trait.strip()}: {desc.strip()}"
                for trait, desc in traits
            ]

        # Fatal flaw
        flaw_section = re.search(
            r'## Passivity as Fatal Flaw.*?### \*\*Not Noble Silence:\*\*(.*?)(?=###|\Z)',
            content, re.DOTALL
        )
        if flaw_section:
            # Extract first few lines as summary
            flaw_text = flaw_section.group(1).strip()
            flaw_lines = [line.strip('- ').strip() for line in flaw_text.split('\n') if line.strip().startswith('-')]
            result["fatal_flaw"] = " ".join(flaw_lines[:3]) if flaw_lines else flaw_text[:300]

        # Voice cadence/syntax
        for stage_match in re.finditer(r'### \*\*Stage \d+.*?\*\*Syntax:\*\*\s+(.*?)(?=\n|$)', content):
            if "voice_cadence" not in result:  # Use first one found
                result["voice_cadence"] = stage_match.group(1).strip()

        # Dialogue samples
        dialogue_section = re.search(r'## ACTUAL DIALOGUE VOICE.*?(?=##|\Z)', content, re.DOTALL)
        if dialogue_section:
            # Extract quoted dialogue
            quotes = re.findall(r'[""](.*?)[""\\]', dialogue_section.group(0))
            result["dialogue_samples"] = quotes[:10]  # First 10 samples

        # Contradictions
        contra_section = re.search(r'## His Contradictions.*?(?=##|\Z)', content, re.DOTALL)
        if contra_section:
            contradictions = re.findall(
                r'### \*\*(.*?)\*\*:\s*(.*?)(?=###|##|\Z)',
                contra_section.group(0), re.DOTALL
            )
            result["contradictions"] = [
                f"{title.strip()}: {desc.strip()[:200]}"
                for title, desc in contradictions
            ]

        return result

    def parse_gestalt(self, file_path: Path) -> Dict[str, Any]:
        """Extract essence from gestalt file"""
        if not file_path.exists():
            return {}

        content = file_path.read_text(encoding='utf-8')
        result = {}

        # Physical presence
        physical_section = re.search(
            r'## How He Moves \(Physical Presence\)(.*?)(?=##|\Z)',
            content, re.DOTALL
        )
        if physical_section:
            # Extract key patterns
            patterns = re.findall(
                r'\*\*(.*?)\*\*(.*?)(?=\*\*|##|\Z)',
                physical_section.group(1), re.DOTALL
            )
            result["physical_presence"] = "; ".join([
                f"{p[0].strip()}: {p[1].strip()[:100]}"
                for p in patterns[:5]  # Top 5 patterns
            ])

        # Emotional chords
        emotional_section = re.search(
            r'## How He Feels \(Emotional Signatures\)(.*?)(?=##|\Z)',
            content, re.DOTALL
        )
        if emotional_section:
            chords = re.findall(
                r'### (.*?):(.*?)(?=###|##|\Z)',
                emotional_section.group(1), re.DOTALL
            )
            result["emotional_chords"] = {
                chord[0].strip(): chord[1].strip()[:200]
                for chord in chords
            }

        # The Ineffable Thing (core identity)
        ineffable_section = re.search(
            r'## The Ineffable Thing.*?(?=##|\Z)',
            content, re.DOTALL
        )
        if ineffable_section:
            # Extract the essence - first few paragraphs
            text = ineffable_section.group(0)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            result["core_identity"] = " ".join(paragraphs[:3])  # First 3 paragraphs

        return result


class ChapterParser:
    """Parse chapters to extract lived experience"""

    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    def __init__(self, chapters_dir: Path):
        self.chapters_dir = chapters_dir

    def find_chapter_files(self) -> List[Path]:
        """Find all chapter markdown files"""
        if not self.chapters_dir.exists():
            return []

        files = []
        for md_file in self.chapters_dir.rglob("*.md"):
            name = md_file.name.lower()
            if not name.startswith("_") and not name.startswith("."):
                files.append(md_file)
        return sorted(files)

    def extract_frontmatter(self, file_path: Path) -> Optional[Dict]:
        """Extract YAML frontmatter from chapter file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            match = self.FRONTMATTER_PATTERN.match(content)
            if not match:
                return None

            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return None

            # Also get content
            frontmatter["_content"] = content[match.end():]
            frontmatter["_file_path"] = str(file_path)

            return frontmatter
        except Exception:
            return None

    def get_pov_chapters(
        self,
        character_name: str,
        as_of_date: Optional[str] = None,
        as_of_chapter: Optional[int] = None
    ) -> List[Dict]:
        """Get all POV chapters for character up to specified point"""
        chapters = []

        for file_path in self.find_chapter_files():
            fm = self.extract_frontmatter(file_path)
            if not fm:
                continue

            # Must be POV for this character
            if fm.get("pov_character", "").lower().strip() != character_name.lower().strip():
                continue

            # Must be groundable (draft/revised/final)
            status = fm.get("status", "").lower()
            if status not in ("draft", "revised", "final"):
                continue

            # Apply date filter
            if as_of_date:
                story_date = fm.get("story_date")
                if story_date and str(story_date) > as_of_date:
                    continue

            # Apply chapter filter
            if as_of_chapter:
                chapter_num = fm.get("chapter_number")
                if chapter_num and chapter_num > as_of_chapter:
                    continue

            chapters.append(fm)

        # Sort by chapter number, then date
        chapters.sort(key=lambda c: (
            c.get("chapter_number", 999),
            str(c.get("story_date", "9999-99-99"))
        ))

        return chapters


class ContinuityParser:
    """Parse Continuity_Tracking files"""

    def __init__(self, continuity_dir: Path):
        self.continuity_dir = continuity_dir

    def get_relationship_state(self, character_name: str, other_character: str) -> Optional[str]:
        """Get relationship state between two characters"""
        if not self.continuity_dir.exists():
            return None

        rel_dir = self.continuity_dir / "Relationship_States"
        if not rel_dir.exists():
            return None

        # Try both orderings
        first = character_name.split()[0]
        other_first = other_character.split()[0]

        patterns = [
            f"{first}-{other_first}.md",
            f"{other_first}-{first}.md",
            f"*{first}*{other_first}*.md",
            f"*{other_first}*{first}*.md",
        ]

        for pattern in patterns:
            matches = list(rel_dir.glob(pattern))
            if matches:
                # Read the file and extract current status
                content = matches[0].read_text(encoding='utf-8')
                # Look for "Current Relationship Status" section
                status_match = re.search(
                    r'## Current Relationship Status.*?(?=##|\Z)',
                    content, re.DOTALL
                )
                if status_match:
                    return status_match.group(0).strip()[:500]

        return None


# =============================================================================
# Character Consciousness Builder
# =============================================================================

class ConsciousnessBuilder:
    """Assembles complete character consciousness"""

    def __init__(
        self,
        characters_dir: Path,
        chapters_dir: Path,
        continuity_dir: Path
    ):
        self.char_parser = CharacterSourceParser(characters_dir)
        self.chapter_parser = ChapterParser(chapters_dir)
        self.continuity_parser = ContinuityParser(continuity_dir)

        self.cache_dir = Path(".cache/character_consciousness")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        character_name: str,
        as_of_date: Optional[str] = None,
        as_of_chapter: Optional[int] = None,
        use_cache: bool = True
    ) -> CharacterConsciousness:
        """Build complete character consciousness"""

        # Check cache
        cache_key = f"{character_name.lower().replace(' ', '_')}_{as_of_date or 'latest'}_{as_of_chapter or 'latest'}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        if use_cache and cache_file.exists():
            print(f"[CACHE] Loading cached consciousness for {character_name}")
            with open(cache_file) as f:
                data = json.load(f)
                return CharacterConsciousness(**data)

        print(f"Building consciousness for {character_name}...")

        # Initialize consciousness
        consciousness = CharacterConsciousness(
            name=character_name,
            canonical_name=character_name,  # TODO: Get from schema
            as_of_date=as_of_date or "latest",
            as_of_chapter=as_of_chapter or 0
        )

        # 1. Extract essence from character files
        char_files = self.char_parser.find_files(character_name)
        print(f"  Found {len(char_files)} character files")

        if "voice_profile" in char_files:
            voice_data = self.char_parser.parse_voice_profile(char_files["voice_profile"])
            consciousness.core_traits = voice_data.get("core_traits", [])
            consciousness.fatal_flaw = voice_data.get("fatal_flaw", "")
            consciousness.voice_cadence = voice_data.get("voice_cadence", "")
            consciousness.dialogue_samples = voice_data.get("dialogue_samples", [])
            consciousness.contradictions = voice_data.get("contradictions", [])

        if "gestalt" in char_files:
            gestalt_data = self.char_parser.parse_gestalt(char_files["gestalt"])
            consciousness.core_identity = gestalt_data.get("core_identity", "")
            consciousness.physical_presence = gestalt_data.get("physical_presence", "")
            consciousness.emotional_chords = gestalt_data.get("emotional_chords", {})

        # 2. Extract lived experience from chapters
        pov_chapters = self.chapter_parser.get_pov_chapters(
            character_name,
            as_of_date=as_of_date,
            as_of_chapter=as_of_chapter
        )
        print(f"  Found {len(pov_chapters)} POV chapters")

        consciousness.chapters_lived = [
            {
                "chapter": ch.get("chapter_number"),
                "date": str(ch.get("story_date", "")),
                "title": ch.get("title", ""),
                "summary": ch.get("summary", ""),
                "content_preview": ch.get("_content", "")[:1000]  # First 1000 chars
            }
            for ch in pov_chapters
        ]

        if pov_chapters:
            consciousness.as_of_chapter = pov_chapters[-1].get("chapter_number", 0)
            consciousness.as_of_date = str(pov_chapters[-1].get("story_date", ""))

        # 3. Synthesize current state
        consciousness.emotional_state_now = self._synthesize_emotional_state(pov_chapters)
        consciousness.immediate_need = self._synthesize_immediate_need(pov_chapters)
        consciousness.how_to_sound = self._synthesize_voice_guidance(consciousness)

        # 4. TODO: Extract knowledge bounds, relationships, continuity
        # (For now, placeholders)

        # Cache it
        with open(cache_file, 'w') as f:
            json.dump(asdict(consciousness), f, indent=2)

        print(f"[OK] Consciousness built and cached")
        return consciousness

    def _synthesize_emotional_state(self, chapters: List[Dict]) -> str:
        """Synthesize current emotional state from recent chapters"""
        if not chapters:
            return "Unknown"

        # Get last 2 chapter summaries
        recent = chapters[-2:]
        summaries = [ch.get("summary", "") for ch in recent]
        return " → ".join(summaries)

    def _synthesize_immediate_need(self, chapters: List[Dict]) -> str:
        """Synthesize what character needs RIGHT NOW"""
        if not chapters:
            return "Unknown"

        # Simple heuristic: extract from last chapter summary
        last_summary = chapters[-1].get("summary", "")
        return f"Based on recent events: {last_summary[:200]}"

    def _synthesize_voice_guidance(self, consciousness: CharacterConsciousness) -> str:
        """Create direct voice guidance for LLM"""
        parts = []

        if consciousness.voice_cadence:
            parts.append(f"Speak with: {consciousness.voice_cadence}")

        if consciousness.core_traits:
            parts.append(f"Core traits: {', '.join(consciousness.core_traits[:3])}")

        if consciousness.fatal_flaw:
            parts.append(f"Fatal flaw active: {consciousness.fatal_flaw[:100]}")

        return " | ".join(parts)


# =============================================================================
# Output Formatters
# =============================================================================

def format_markdown(consciousness: CharacterConsciousness) -> str:
    """Format consciousness as human-readable markdown"""
    md = f"""# {consciousness.canonical_name} - Character Consciousness

**As of:** {consciousness.as_of_date} (Chapter {consciousness.as_of_chapter})

---

## Core Identity

{consciousness.core_identity}

### Core Traits (Never Change)
"""
    for trait in consciousness.core_traits:
        md += f"- {trait}\n"

    md += f"""
### Fatal Flaw
{consciousness.fatal_flaw}

### Contradictions
"""
    for contra in consciousness.contradictions:
        md += f"- {contra}\n"

    md += f"""
---

## Voice & Expression

**Cadence:** {consciousness.voice_cadence}

**Physical Presence:** {consciousness.physical_presence}

**Dialogue Samples:**
"""
    for sample in consciousness.dialogue_samples[:5]:
        md += f'- "{sample}"\n'

    md += f"""
---

## Current State

**Emotional State:** {consciousness.emotional_state_now}

**Immediate Need:** {consciousness.immediate_need}

**How to Sound:** {consciousness.how_to_sound}

---

## Lived Experience

**Total chapters experienced:** {len(consciousness.chapters_lived)}

"""
    for ch in consciousness.chapters_lived:
        md += f"### Chapter {ch['chapter']}: {ch['title']} ({ch['date']})\n"
        md += f"{ch['summary']}\n\n"

    return md


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Build complete character consciousness for roleplay"
    )
    parser.add_argument(
        "--character",
        required=True,
        help="Character name (e.g., 'Santiago Esposito')"
    )
    parser.add_argument(
        "--date",
        help="Story date to ground at (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--chapter",
        type=int,
        help="Chapter number to ground at"
    )
    parser.add_argument(
        "--characters-dir",
        type=Path,
        default=None,
        help="Path to Characters directory"
    )
    parser.add_argument(
        "--chapters-dir",
        type=Path,
        default=None,
        help="Path to chapters directory"
    )
    parser.add_argument(
        "--continuity-dir",
        type=Path,
        default=None,
        help="Path to Continuity_Tracking directory"
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Output JSON file for LLM"
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        help="Output markdown file for human"
    )
    parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Rebuild cache even if exists"
    )

    args = parser.parse_args()

    # Build consciousness
    builder = ConsciousnessBuilder(
        characters_dir=args.characters_dir,
        chapters_dir=args.chapters_dir,
        continuity_dir=args.continuity_dir
    )

    consciousness = builder.build(
        character_name=args.character,
        as_of_date=args.date,
        as_of_chapter=args.chapter,
        use_cache=not args.rebuild_cache
    )

    # Output JSON (for LLM)
    json_output = json.dumps(asdict(consciousness), indent=2)
    if args.output_json:
        args.output_json.write_text(json_output, encoding='utf-8')
        print(f"[OK] JSON written to {args.output_json}")
    else:
        print("\n=== JSON OUTPUT (for LLM) ===")
        print(json_output)

    # Output Markdown (for human)
    md_output = format_markdown(consciousness)
    if args.output_md:
        args.output_md.write_text(md_output, encoding='utf-8')
        print(f"[OK] Markdown written to {args.output_md}")
    else:
        print("\n=== MARKDOWN OUTPUT (for Human) ===")
        print(md_output)


if __name__ == "__main__":
    main()
