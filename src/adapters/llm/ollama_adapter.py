"""
Ollama LLM Adapter - Local model implementation.

This adapter implements the LLMAdapter port for Ollama-hosted models
(Qwen, Llama, etc.) running locally or on a private server.
"""
import json
import time
import requests
from typing import Optional

from src.ports.llm_adapter import LLMAdapter, LLMConfig
from src.domain.models import CharacterProfile, ValidationResult, FlaggedPassage


class OllamaAdapter(LLMAdapter):
    """
    Adapter for Ollama-hosted local LLM models.

    Supports any model available in Ollama (Qwen, Llama, Mistral, etc.).
    Communicates via Ollama's REST API for voice validation tasks.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize Ollama adapter.

        Args:
            config: LLMConfig with Ollama-specific settings
        """
        super().__init__(config)

        # Default to local Ollama instance if no base_url provided
        self.base_url = config.base_url or "http://localhost:11434"
        self.api_endpoint = f"{self.base_url}/api/generate"
        self.tags_endpoint = f"{self.base_url}/api/tags"

    def validate_voice(
        self,
        profile: CharacterProfile,
        excerpt: str,
        chapter: Optional[int] = None,
        context: Optional[str] = None,
        pre_context: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate text excerpt using Ollama.

        Args:
            profile: Character profile with voice characteristics
            excerpt: Text to validate
            chapter: Optional chapter number for arc stage detection
            context: Optional scene context
            pre_context: Optional pre-computed deterministic findings injected before
                the excerpt, instructing the model not to re-flag already-caught violations

        Returns:
            ValidationResult with validation details

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If API call fails
            TimeoutError: If API call times out
        """
        if not excerpt or not excerpt.strip():
            raise ValueError("Excerpt cannot be empty")

        start_time = time.time()

        # Get appropriate arc stage if chapter provided
        arc_stage = None
        arc_stage_id = None
        if chapter is not None:
            arc_stage = profile.get_arc_stage(chapter=chapter)
            arc_stage_id = arc_stage.stage_id if arc_stage else None

        # Construct the validation prompt (reuse Claude's prompt builder)
        prompt = self._build_validation_prompt(
            profile=profile,
            excerpt=excerpt,
            arc_stage=arc_stage,
            context=context,
            pre_context=pre_context,
        )

        # Call Ollama API
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    }
                },
                timeout=self.config.timeout_seconds
            )

            response.raise_for_status()
            response_data = response.json()
            response_text = response_data.get("response", "")

            # Parse response
            validation_data = self._parse_validation_response(response_text)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            # Build ValidationResult
            result = ValidationResult(
                character_name=profile.name,
                excerpt=excerpt,
                is_valid=validation_data["is_valid"],
                confidence_score=validation_data["confidence_score"],
                severity=validation_data["severity"],
                flagged_passages=validation_data.get("flagged_passages"),
                arc_stage_used=arc_stage_id,
                model_used=self.config.model_name,
                summary=validation_data.get("summary"),
                suggestions=validation_data.get("suggestions"),
                processing_time_ms=processing_time
            )

            return result

        except requests.Timeout:
            raise TimeoutError(
                f"Ollama API timeout after {self.config.timeout_seconds}s"
            )
        except requests.ConnectionError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Is Ollama running? Error: {str(e)}"
            )
        except requests.HTTPError as e:
            raise RuntimeError(f"Ollama API HTTP error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during validation: {str(e)}")

    def health_check(self) -> bool:
        """
        Check if Ollama is running and model is available.

        Returns:
            True if Ollama is responding and model exists, False otherwise
        """
        try:
            # Check if Ollama is running
            response = requests.get(
                self.tags_endpoint,
                timeout=5
            )
            response.raise_for_status()

            # Check if our model is available
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]

            # Model name might have :latest or other tags
            model_available = any(
                self.config.model_name in model_name
                for model_name in models
            )

            return model_available

        except Exception:
            return False

    def _build_validation_prompt(
        self,
        profile: CharacterProfile,
        excerpt: str,
        arc_stage: Optional[object] = None,
        context: Optional[str] = None,
        pre_context: Optional[str] = None
    ) -> str:
        """
        Build the validation prompt for Ollama.

        Uses the same prompt structure as Claude adapter for consistency.

        Args:
            profile: Character profile
            excerpt: Text to validate
            arc_stage: Optional arc stage object
            context: Optional scene context
            pre_context: Optional pre-computed rule violations

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are an expert character voice validator for creative writing.",
            "Your task is to validate whether a text excerpt matches a character's established voice.",
            "",
            f"# Character: {profile.name}",
        ]

        # Add basic traits if available
        if profile.basic_traits:
            prompt_parts.extend([
                "",
                "## Core Traits:",
                ", ".join(profile.basic_traits)
            ])

        # Add arc stage specific voice characteristics
        if arc_stage:
            prompt_parts.extend([
                "",
                f"## Current Arc Stage: {arc_stage.name}",
            ])
            if arc_stage.vocabulary_register:
                prompt_parts.append(f"Vocabulary: {arc_stage.vocabulary_register}")
            if arc_stage.emotional_tone:
                prompt_parts.append(f"Emotional Tone: {arc_stage.emotional_tone}")
            if arc_stage.speech_patterns:
                prompt_parts.extend([
                    "",
                    "### Speech Patterns:",
                    *[f"- {pattern}" for pattern in arc_stage.speech_patterns]
                ])
            if arc_stage.typical_phrases:
                prompt_parts.extend([
                    "",
                    "### Typical Phrases:",
                    *[f"- {phrase}" for phrase in arc_stage.typical_phrases]
                ])
            if arc_stage.forbidden_patterns:
                prompt_parts.extend([
                    "",
                    "### FORBIDDEN (character would NEVER use):",
                    *[f"- {pattern}" for pattern in arc_stage.forbidden_patterns]
                ])

        # Add global forbidden vocabulary
        if profile.forbidden_vocabulary:
            prompt_parts.extend([
                "",
                "## Forbidden Vocabulary (NEVER used by this character):",
                *[f"- {word}" for word in profile.forbidden_vocabulary]
            ])

        # Add signature phrases
        if profile.signature_phrases:
            prompt_parts.extend([
                "",
                "## Signature Phrases (frequently used):",
                *[f"- {phrase}" for phrase in profile.signature_phrases]
            ])

        # Add voice samples if available
        if profile.voice_samples:
            relevant_samples = (
                profile.get_voice_samples_for_stage(arc_stage.stage_id)
                if arc_stage
                else profile.voice_samples[:3]  # Use first 3 if no stage
            )
            if relevant_samples:
                prompt_parts.extend([
                    "",
                    "## Voice Examples:",
                ])
                for i, sample in enumerate(relevant_samples, 1):
                    prompt_parts.append(f"{i}. \"{sample.text}\"")
                    if sample.context:
                        prompt_parts.append(f"   Context: {sample.context}")

        # Add context if provided
        if context:
            prompt_parts.extend([
                "",
                f"## Scene Context:",
                context
            ])

        # Add pre-computed findings if provided
        if pre_context:
            prompt_parts.extend([
                "",
                "## Pre-Computed Rule Violations (confidence: 1.0)",
                pre_context,
                "",
                "Assess only what the rules above did NOT already catch. Do not re-flag items already listed above."
            ])

        # Add excerpt to validate
        prompt_parts.extend([
            "",
            "## Excerpt to Validate",
            "",
            excerpt,
            "",
            "# Your Task:",
            "Analyze the excerpt and determine if it matches this character's voice.",
            "Return your analysis as a JSON object with this EXACT structure:",
            "```json",
            "{",
            '  "is_valid": true or false,',
            '  "confidence_score": 0.0 to 1.0,',
            '  "severity": "passed" | "info" | "moderate" | "critical",',
            '  "summary": "Brief overall assessment",',
            '  "flagged_passages": [',
            '    {',
            '      "text": "exact text from excerpt",',
            '      "reason": "why this is problematic",',
            '      "severity": "critical" | "moderate" | "info",',
            '      "suggestion": "how to fix it"',
            '    }',
            '  ],',
            '  "suggestions": ["general suggestion 1", "general suggestion 2"]',
            "}",
            "```",
            "",
            "IMPORTANT: Respond ONLY with the JSON object. Do not include any explanatory text before or after.",
            "Be thorough but constructive. Focus on voice consistency, not grammar or style preferences."
        ])

        return "\n".join(prompt_parts)

    def _parse_validation_response(self, response_text: str) -> dict:
        """
        Parse Ollama's response into structured validation data.

        Args:
            response_text: Raw text response from Ollama

        Returns:
            Dict with validation data

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response
        try:
            # Try to find JSON in markdown code blocks
            if "```json" in response_text:
                start = response_text.index("```json") + 7
                end = response_text.index("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.index("```") + 3
                end = response_text.index("```", start)
                json_str = response_text[start:end].strip()
            else:
                # Try to find JSON object boundaries
                if "{" in response_text and "}" in response_text:
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                else:
                    json_str = response_text.strip()

            data = json.loads(json_str)

            # Convert flagged_passages dicts to FlaggedPassage objects
            if "flagged_passages" in data and data["flagged_passages"]:
                data["flagged_passages"] = [
                    FlaggedPassage(**passage)
                    for passage in data["flagged_passages"]
                ]

            # Ensure required fields exist
            if "is_valid" not in data or "confidence_score" not in data:
                raise ValueError("Response missing required fields")

            # Ensure severity is set
            if "severity" not in data or data["severity"] is None:
                if data["is_valid"]:
                    data["severity"] = "passed"
                elif data.get("flagged_passages"):
                    # Get highest severity from flagged passages
                    severities = [p.severity for p in data["flagged_passages"]]
                    if "critical" in severities:
                        data["severity"] = "critical"
                    elif "moderate" in severities:
                        data["severity"] = "moderate"
                    else:
                        data["severity"] = "info"
                else:
                    data["severity"] = "info"

            return data

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse Ollama response as JSON: {str(e)}\n"
                f"Response was: {response_text[:500]}"
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid response structure: {str(e)}")
