import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from openai import OpenAI
import os

log = logging.getLogger("video-engine")

class Language(Enum):
    ENGLISH = "English"
    FRENCH = "French"
    HINDI = "Hindi"
    GUJARATI = "Gujarati"

@dataclass
class ScriptBeat:
    text: str
    visual_prompt: str
    duration_estimate: float
    emotion: str

@dataclass
class VideoScript:
    title: str
    language: str
    duration_mode: str  # "30s", "45s", "60s"
    hook: str
    beats: List[ScriptBeat]
    cta: str

class ScriptGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_SCRIPT_MODEL", "gpt-4o")

    def generate_script(self, topic: str, language: Language, duration: str) -> VideoScript:
        log.info(f"📝 Generating {duration} script in {language.value} for: {topic}")
        
        word_counts = {
            "30s": 70,
            "45s": 110,
            "60s": 140
        }
        target_words = word_counts.get(duration, 70)

        system_prompt = f"""You are an expert viral video screenwriter for YouTube Shorts and Reels.
        Create a high-retention, cinematic script in {language.value}.
        
        Target Duration: {duration} (approx {target_words} spoken words).
        Language: {language.value} (Ensure native, natural phrasing).
        
        Structure:
        1. Hook (0-3s): Grab attention immediately.
        2. Body (Beats): Fast-paced, visual storytelling.
        3. CTA: Strong ending.

        For each beat, provide:
        - 'text': The spoken narration in {language.value}.
        - 'visual_prompt': A detailed English description for an AI image generator (DALL-E 3).
          
          CRITICAL VISUAL RULES:
          1. MUST describe a CONCRETE SCENE with specific SUBJECTS (people, objects, places).
          2. MUST describe ACTION and CONTEXT (what are they doing? where are they?).
          3. FORBIDDEN WORDS: "abstract", "gradient", "background", "pattern", "bokeh", "blur", "noise".
          4. NO metaphorical concepts like "flying numbers" or "glowing networks" unless part of a real scene.
          5. Style: Cinematic, photorealistic, 16:9, high detail.

          Examples of GOOD prompts:
          - "A young content creator in a dimly lit studio editing videos on a holographic screen, cinematic lighting"
          - "A futuristic robot hand shaking a human hand in a corporate boardroom, ultra realistic"
          - "A drone flying over a smart city with neon billboards at night, 8k resolution"

          Examples of BAD prompts (DO NOT USE):
          - "Abstract colorful gradient"
          - "Blue background with lines"
          - "Digital network connections"

        - 'emotion': The mood (e.g., 'epic', 'calm', 'intense').

        Return STRICT JSON format:
        {{
            "title": "Video Title",
            "hook": "Spoken hook text",
            "beats": [
                {{"text": "Spoken text", "visual_prompt": "CONCRETE visual description", "emotion": "mood"}}
            ],
            "cta": "Spoken CTA"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a script about: {topic}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            data = json.loads(response.choices[0].message.content)
            
            beats = []
            for b in data.get("beats", []):
                beats.append(ScriptBeat(
                    text=b["text"],
                    visual_prompt=b["visual_prompt"],
                    duration_estimate=len(b["text"].split()) / 2.5, # Rough estimate
                    emotion=b.get("emotion", "neutral")
                ))

            return VideoScript(
                title=data.get("title", "Untitled"),
                language=language.value,
                duration_mode=duration,
                hook=data.get("hook", ""),
                beats=beats,
                cta=data.get("cta", "")
            )

        except Exception as e:
            log.error(f"Script generation failed: {e}")
            raise
