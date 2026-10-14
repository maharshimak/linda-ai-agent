"""
Prompt Interpreter
NLP-based scene planning that transforms user prompts into structured scene breakdowns.
"""
import json
import logging
from typing import List, Optional
from dataclasses import dataclass

from openai import OpenAI

from ..models import ScriptBeat, VideoScript, Language, Emotion, CameraMove

log = logging.getLogger("core.ai.prompt_interpreter")


SCENE_PLANNER_SYSTEM = """You are an expert AI video director and screenwriter.
Your job is to transform a user's topic or script into a structured video plan.

Analyze the input and break it into distinct SCENES (beats) that will form a compelling video narrative.

For each scene, determine:
1. The spoken narration text
2. A detailed visual prompt for AI image generation
3. The emotional tone (calm, intense, mysterious, uplifting, epic, suspense, joy, melancholy, neutral)
4. Suggested camera movement (dolly_in, dolly_out, pan_left, pan_right, crane_up, crane_down, orbit, parallax, static)

CRITICAL VISUAL PROMPT RULES:
- MUST describe a CONCRETE SCENE with specific subjects (people, objects, places)
- MUST describe ACTION and CONTEXT (what are they doing? where are they?)
- FORBIDDEN: "abstract", "gradient", "background only", "pattern", "bokeh"
- Style: Cinematic, photorealistic, 16:9, high detail

Return STRICT JSON:
{
    "title": "Compelling video title",
    "hook": "Attention-grabbing opening line (5-8 words)",
    "beats": [
        {
            "text": "Spoken narration text",
            "visual_prompt": "Detailed visual description for AI image generation",
            "emotion": "emotional_tone",
            "camera_move": "camera_movement",
            "setting": "Location/environment description",
            "characters": ["list of characters if any"],
            "key_actions": ["action1", "action2"]
        }
    ],
    "cta": "Call-to-action closing line",
    "theme": "epic|mysterious|inspiring|intense|peaceful",
    "pacing_notes": "Overall pacing suggestions"
}
"""


class PromptInterpreter:
    """
    Transforms user prompts into structured scene plans.
    The first step in the AI Creative Intelligence pipeline.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def interpret(
        self, 
        topic: str, 
        language: Language = Language.ENGLISH,
        duration: str = "30s",
        style: Optional[str] = None
    ) -> VideoScript:
        """
        Interpret a topic/prompt and generate a structured video script.
        
        Args:
            topic: User's topic, prompt, or script
            language: Target language for narration
            duration: Target duration ("30s", "45s", "60s")
            style: Optional style hint
            
        Returns:
            VideoScript with structured beats
        """
        log.info(f"🧠 Interpreting prompt: {topic[:80]}...")
        
        # Calculate word targets based on duration
        word_targets = {"30s": 70, "45s": 110, "60s": 140}
        target_words = word_targets.get(duration, 70)
        beat_count = {"30s": 3, "45s": 4, "60s": 5}.get(duration, 3)
        
        user_prompt = f"""Create a {duration} video script about: "{topic}"

Target: {target_words} spoken words total, {beat_count} distinct scenes/beats.
Language: {language.value}
{f'Style hint: {style}' if style else ''}

Make it cinematic, engaging, and visually striking."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCENE_PLANNER_SYSTEM},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            data = json.loads(response.choices[0].message.content)
            
            # Parse beats
            beats = []
            for b in data.get("beats", []):
                # Map emotion string to enum
                emotion_str = b.get("emotion", "neutral").lower()
                try:
                    emotion = Emotion(emotion_str)
                except ValueError:
                    emotion = Emotion.NEUTRAL
                
                # Map camera move string to enum
                camera_str = b.get("camera_move", "dolly_in").lower()
                try:
                    camera_move = CameraMove(camera_str)
                except ValueError:
                    camera_move = CameraMove.DOLLY_IN
                
                beats.append(ScriptBeat(
                    text=b["text"],
                    visual_prompt=b["visual_prompt"],
                    duration_estimate=len(b["text"].split()) / 2.5,
                    emotion=emotion,
                    camera_move=camera_move,
                    setting=b.get("setting"),
                    characters=b.get("characters"),
                    key_actions=b.get("key_actions")
                ))
            
            script = VideoScript(
                title=data.get("title", "Untitled"),
                language=language.value,
                duration_mode=duration,
                hook=data.get("hook", ""),
                beats=beats,
                cta=data.get("cta", ""),
                theme=data.get("theme", "epic")
            )
            
            log.info(f"✅ Generated script: '{script.title}' with {len(beats)} scenes")
            return script
            
        except Exception as e:
            log.error(f"Prompt interpretation failed: {e}")
            raise
    
    def refine_script(self, script: VideoScript, feedback: str) -> VideoScript:
        """
        Refine an existing script based on user feedback.
        Enables iterative improvement loop.
        """
        log.info(f"🔄 Refining script based on feedback...")
        
        current_json = {
            "title": script.title,
            "hook": script.hook,
            "beats": [
                {
                    "text": b.text,
                    "visual_prompt": b.visual_prompt,
                    "emotion": b.emotion.value,
                    "camera_move": b.camera_move.value
                }
                for b in script.beats
            ],
            "cta": script.cta,
            "theme": script.theme
        }
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SCENE_PLANNER_SYSTEM},
                {"role": "user", "content": f"Current script:\n{json.dumps(current_json, indent=2)}"},
                {"role": "user", "content": f"User feedback: {feedback}\n\nRefine the script accordingly."}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        
        # Parse refined script (same as interpret)
        data = json.loads(response.choices[0].message.content)
        
        beats = []
        for b in data.get("beats", []):
            emotion_str = b.get("emotion", "neutral").lower()
            try:
                emotion = Emotion(emotion_str)
            except ValueError:
                emotion = Emotion.NEUTRAL
                
            camera_str = b.get("camera_move", "dolly_in").lower()
            try:
                camera_move = CameraMove(camera_str)
            except ValueError:
                camera_move = CameraMove.DOLLY_IN
            
            beats.append(ScriptBeat(
                text=b["text"],
                visual_prompt=b["visual_prompt"],
                duration_estimate=len(b["text"].split()) / 2.5,
                emotion=emotion,
                camera_move=camera_move
            ))
        
        return VideoScript(
            title=data.get("title", script.title),
            language=script.language,
            duration_mode=script.duration_mode,
            hook=data.get("hook", script.hook),
            beats=beats,
            cta=data.get("cta", script.cta),
            theme=data.get("theme", script.theme)
        )
