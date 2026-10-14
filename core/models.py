"""
Core Data Models
Shared data structures for the video generation pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Language(Enum):
    """Supported languages for narration."""
    ENGLISH = "English"
    FRENCH = "French"
    HINDI = "Hindi"
    GUJARATI = "Gujarati"


class CameraMove(Enum):
    """Available camera movements."""
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    ORBIT = "orbit"
    PARALLAX = "parallax"
    DUTCH_ANGLE = "dutch"
    STATIC = "static"


class Emotion(Enum):
    """Emotional tones for scenes."""
    CALM = "calm"
    INTENSE = "intense"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"
    EPIC = "epic"
    SUSPENSE = "suspense"
    JOY = "joy"
    MELANCHOLY = "melancholy"
    NEUTRAL = "neutral"


class ColorPalette(Enum):
    """Cinematic color palettes."""
    BLOCKBUSTER = {
        "primary": (255, 147, 41),    # Orange
        "secondary": (0, 174, 239),   # Teal
        "accent": (255, 215, 0),      # Gold
        "text": (255, 255, 255),
        "shadow": (0, 20, 40)
    }
    NOIR = {
        "primary": (200, 200, 220),
        "secondary": (100, 100, 120),
        "accent": (255, 50, 50),
        "text": (240, 240, 240),
        "shadow": (10, 10, 20)
    }
    NEON = {
        "primary": (255, 0, 255),
        "secondary": (0, 255, 255),
        "accent": (255, 255, 0),
        "text": (255, 255, 255),
        "shadow": (0, 0, 0)
    }
    EARTHY = {
        "primary": (139, 90, 60),
        "secondary": (107, 142, 35),
        "accent": (255, 140, 0),
        "text": (255, 248, 220),
        "shadow": (40, 30, 20)
    }
    MINIMAL = {
        "primary": (60, 60, 60),
        "secondary": (120, 120, 120),
        "accent": (0, 122, 255),
        "text": (255, 255, 255),
        "shadow": (20, 20, 20)
    }


@dataclass
class ScriptBeat:
    """A single beat/scene in the video script."""
    text: str
    visual_prompt: str
    duration_estimate: float = 4.0
    emotion: Emotion = Emotion.NEUTRAL
    camera_move: CameraMove = CameraMove.DOLLY_IN
    
    # AI-generated enrichments
    setting: Optional[str] = None
    characters: Optional[List[str]] = None
    key_actions: Optional[List[str]] = None


@dataclass
class VideoScript:
    """Complete video script with metadata."""
    title: str
    language: str
    duration_mode: str  # "30s", "45s", "60s"
    hook: str
    beats: List[ScriptBeat]
    cta: str
    
    # Style metadata
    theme: str = "epic"
    palette: ColorPalette = ColorPalette.BLOCKBUSTER
    emotions: List[str] = field(default_factory=list)
    visual_notes: List[str] = field(default_factory=list)


@dataclass
class GenerationContext:
    """Context passed through the generation pipeline."""
    script: VideoScript
    output_dir: str
    
    # Generated assets
    images: List[str] = field(default_factory=list)
    audio_segments: List[str] = field(default_factory=list)
    voice_path: Optional[str] = None
    music_path: Optional[str] = None
    
    # Timing info
    beat_timings: List[Dict[str, float]] = field(default_factory=list)
    total_duration: float = 0.0
    
    # Quality metrics
    quality_scores: Dict[str, float] = field(default_factory=dict)
