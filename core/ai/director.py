"""
AI Director Mode for MAK AI
AI-powered cinematic decision making for video generation.

Features:
- Script analysis for directorial choices
- Pacing decisions (fast-cut vs slow burn)
- Color palette selection per act
- Camera movement recommendations
- Music cue mapping
- Emotional arc visualization
"""

import logging
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

log = logging.getLogger("ai_director")


class PacingStyle(Enum):
    """Video pacing styles"""
    FAST = "fast"              # Quick cuts, high energy
    SLOW = "slow"              # Lingering shots, contemplative
    VARIED = "varied"          # Mix based on content
    RHYTHMIC = "rhythmic"      # Synced to music beat
    BUILDING = "building"      # Starts slow, accelerates


class CameraStyle(Enum):
    """Camera movement styles"""
    STATIC = "static"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    HANDHELD = "handheld"
    AERIAL = "aerial"
    TRACKING = "tracking"
    ZOOM_SLOW = "zoom_slow"
    ZOOM_FAST = "zoom_fast"


class ColorMood(Enum):
    """Color grading moods"""
    WARM = "warm"               # Golden, amber tones
    COOL = "cool"               # Blue, cyan tones
    CINEMATIC = "cinematic"     # Teal and orange
    NOIR = "noir"               # High contrast B&W leaning
    DREAMY = "dreamy"           # Soft pastels, low contrast
    VIBRANT = "vibrant"         # Saturated, punchy colors
    DESATURATED = "desaturated" # Muted, documentary feel
    VINTAGE = "vintage"         # Faded, film-like


@dataclass
class PacingDecision:
    """Pacing analysis result"""
    rhythm: PacingStyle
    avg_shot_length: float  # seconds
    confidence: float
    reasoning: str


@dataclass
class ColorDecision:
    """Color palette decision"""
    primary: str           # Hex color
    secondary: str         # Hex color
    accent: str            # Hex color
    mood: ColorMood
    lut_suggestion: Optional[str] = None
    reasoning: str = ""


@dataclass
class CameraDecision:
    """Camera movement for a scene"""
    scene_index: int
    movement: CameraStyle
    speed: float = 1.0     # 0.5 = slow, 1.0 = normal, 2.0 = fast
    reasoning: str = ""


@dataclass
class MusicCue:
    """Music timing cue"""
    timestamp: float       # seconds
    action: str            # "fade_in", "build", "drop", "fade_out"
    intensity: float       # 0.0 - 1.0
    description: str = ""


@dataclass
class EmotionalBeat:
    """Emotional arc point"""
    timestamp: float
    emotion: str
    intensity: float       # 0.0 - 1.0
    description: str = ""


@dataclass
class DirectorVision:
    """Complete directorial vision for a video"""
    pacing: PacingDecision
    color_palette: ColorDecision
    camera_movements: List[CameraDecision]
    music_map: List[MusicCue]
    emotional_arc: List[EmotionalBeat]
    visual_metaphors: List[Dict[str, str]]
    overall_style: str
    confidence: float


class AIDirector:
    """
    AI Director that makes cinematic decisions for video generation.
    
    Analyzes scripts and makes creative choices like a human director would,
    including pacing, camera movements, color grading, and music timing.
    """
    
    # Keyword to emotion mapping
    EMOTION_KEYWORDS = {
        "epic": [
            "war", "battle", "conquer", "triumph", "victory", "hero", "glory",
            "empire", "legendary", "mighty", "power", "ancient", "rise", "fall"
        ],
        "calm": [
            "peace", "serene", "gentle", "quiet", "soft", "tranquil", "still",
            "meditation", "nature", "flowing", "breeze", "harmony"
        ],
        "mysterious": [
            "secret", "hidden", "unknown", "darkness", "shadow", "enigma",
            "whisper", "ancient", "forgotten", "cryptic", "riddle"
        ],
        "intense": [
            "urgent", "critical", "danger", "crisis", "fight", "struggle",
            "conflict", "tension", "pressure", "desperate", "survive"
        ],
        "emotional": [
            "love", "loss", "memory", "heart", "tears", "hope", "dream",
            "sacrifice", "bond", "farewell", "reunion", "remember"
        ],
        "uplifting": [
            "inspire", "achieve", "dream", "believe", "overcome", "success",
            "future", "possibility", "change", "breakthrough", "new"
        ],
        "dark": [
            "death", "doom", "destruction", "horror", "terror", "fear",
            "nightmare", "evil", "corrupt", "decay", "end"
        ]
    }
    
    # Color palettes for moods
    COLOR_PALETTES = {
        "epic": {
            "primary": "#1a1a2e",      # Deep navy
            "secondary": "#c9a227",    # Gold
            "accent": "#8b0000",       # Deep red
            "mood": ColorMood.CINEMATIC
        },
        "calm": {
            "primary": "#e8f4f8",      # Soft blue-white
            "secondary": "#a8d5ba",    # Sage green
            "accent": "#f7dc6f",       # Soft yellow
            "mood": ColorMood.DREAMY
        },
        "mysterious": {
            "primary": "#0d0d0d",      # Near black
            "secondary": "#4a0080",    # Deep purple
            "accent": "#00ff88",       # Neon green
            "mood": ColorMood.NOIR
        },
        "intense": {
            "primary": "#1c1c1c",      # Dark gray
            "secondary": "#ff4444",    # Bright red
            "accent": "#ffaa00",       # Orange
            "mood": ColorMood.VIBRANT
        },
        "emotional": {
            "primary": "#2c1810",      # Warm brown
            "secondary": "#e6b8a2",    # Soft peach
            "accent": "#d4a574",       # Golden tan
            "mood": ColorMood.WARM
        },
        "uplifting": {
            "primary": "#fff9e6",      # Warm white
            "secondary": "#ffd700",    # Gold
            "accent": "#ff6b35",       # Coral
            "mood": ColorMood.WARM
        },
        "dark": {
            "primary": "#000000",      # Pure black
            "secondary": "#1a1a2e",    # Navy black
            "accent": "#4a0000",       # Blood red
            "mood": ColorMood.NOIR
        },
        "neutral": {
            "primary": "#1a1a2e",      # Standard cinematic
            "secondary": "#16a085",    # Teal
            "accent": "#e67e22",       # Orange
            "mood": ColorMood.CINEMATIC
        }
    }
    
    # Pacing rules
    PACING_RULES = {
        "epic": PacingStyle.BUILDING,
        "calm": PacingStyle.SLOW,
        "mysterious": PacingStyle.VARIED,
        "intense": PacingStyle.FAST,
        "emotional": PacingStyle.SLOW,
        "uplifting": PacingStyle.BUILDING,
        "dark": PacingStyle.VARIED
    }
    
    # Shot length by pacing
    SHOT_LENGTHS = {
        PacingStyle.FAST: 2.5,
        PacingStyle.SLOW: 6.0,
        PacingStyle.VARIED: 4.0,
        PacingStyle.RHYTHMIC: 3.5,
        PacingStyle.BUILDING: 4.5
    }
    
    def __init__(self):
        """Initialize AI Director"""
        log.info("🎬 AI Director initialized - Ready to make cinematic magic!")
    
    async def analyze_script(self, script: str, scenes: Optional[List[dict]] = None) -> DirectorVision:
        """
        Perform deep analysis of script and make directorial decisions.
        
        Args:
            script: Full script text or topic
            scenes: Optional pre-parsed scenes
            
        Returns:
            DirectorVision with all creative decisions
        """
        log.info(f"🎬 AI Director analyzing script ({len(script)} chars)...")
        
        # 1. Detect dominant emotion
        dominant_emotion = self._detect_dominant_emotion(script)
        
        # 2. Pacing decision
        pacing = self._decide_pacing(script, dominant_emotion)
        
        # 3. Color palette
        colors = self._decide_colors(dominant_emotion, script)
        
        # 4. Camera movements (if scenes provided)
        camera_movements = []
        if scenes:
            camera_movements = self._plan_camera_movements(scenes)
        
        # 5. Music map
        music_map = self._create_music_map(script, scenes, pacing)
        
        # 6. Emotional arc
        emotional_arc = self._map_emotional_arc(script, scenes)
        
        # 7. Visual metaphors
        visual_metaphors = self._suggest_visual_metaphors(script, dominant_emotion)
        
        # 8. Overall style
        overall_style = self._determine_overall_style(dominant_emotion, pacing)
        
        vision = DirectorVision(
            pacing=pacing,
            color_palette=colors,
            camera_movements=camera_movements,
            music_map=music_map,
            emotional_arc=emotional_arc,
            visual_metaphors=visual_metaphors,
            overall_style=overall_style,
            confidence=0.85
        )
        
        log.info(f"🎬 Director's Vision: {overall_style} style, {pacing.rhythm.value} pacing")
        
        return vision
    
    def _detect_dominant_emotion(self, script: str) -> str:
        """Detect the dominant emotion in the script"""
        script_lower = script.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in script_lower)
            emotion_scores[emotion] = score
        
        if max(emotion_scores.values()) == 0:
            return "neutral"
        
        return max(emotion_scores, key=emotion_scores.get)
    
    def _decide_pacing(self, script: str, emotion: str) -> PacingDecision:
        """Decide video pacing based on content"""
        # Get base pacing from emotion
        rhythm = self.PACING_RULES.get(emotion, PacingStyle.VARIED)
        
        # Adjust based on script characteristics
        word_count = len(script.split())
        
        # Short scripts = faster pacing
        if word_count < 50:
            rhythm = PacingStyle.FAST
        elif word_count > 200:
            rhythm = PacingStyle.BUILDING
        
        # Check for action keywords that suggest faster pacing
        action_words = ["suddenly", "crash", "explode", "rush", "race", "quick"]
        if any(word in script.lower() for word in action_words):
            if rhythm == PacingStyle.SLOW:
                rhythm = PacingStyle.VARIED
        
        avg_shot_length = self.SHOT_LENGTHS[rhythm]
        
        reasoning = f"Based on {emotion} mood and {word_count} words"
        
        return PacingDecision(
            rhythm=rhythm,
            avg_shot_length=avg_shot_length,
            confidence=0.85,
            reasoning=reasoning
        )
    
    def _decide_colors(self, emotion: str, script: str) -> ColorDecision:
        """Select color palette for the video"""
        palette = self.COLOR_PALETTES.get(emotion, self.COLOR_PALETTES["neutral"])
        
        # Check for specific color mentions in script
        script_lower = script.lower()
        
        # Adjust if specific environments are mentioned
        if any(word in script_lower for word in ["ocean", "sea", "water", "ice"]):
            palette["secondary"] = "#0077be"  # Ocean blue
        elif any(word in script_lower for word in ["fire", "volcano", "desert", "sun"]):
            palette["secondary"] = "#ff4500"  # Orange-red
        elif any(word in script_lower for word in ["forest", "nature", "garden", "green"]):
            palette["secondary"] = "#228b22"  # Forest green
        
        return ColorDecision(
            primary=palette["primary"],
            secondary=palette["secondary"],
            accent=palette.get("accent", "#ffffff"),
            mood=palette["mood"],
            lut_suggestion=self._suggest_lut(palette["mood"]),
            reasoning=f"Color palette for {emotion} mood"
        )
    
    def _suggest_lut(self, mood: ColorMood) -> Optional[str]:
        """Suggest a LUT file for color grading"""
        lut_map = {
            ColorMood.CINEMATIC: "teal_orange_cinema.cube",
            ColorMood.WARM: "golden_hour.cube",
            ColorMood.COOL: "arctic_blue.cube",
            ColorMood.NOIR: "high_contrast_bw.cube",
            ColorMood.DREAMY: "soft_pastel.cube",
            ColorMood.VINTAGE: "kodak_film.cube",
            ColorMood.VIBRANT: "punch_saturate.cube",
            ColorMood.DESATURATED: "bleach_bypass.cube"
        }
        return lut_map.get(mood)
    
    def _plan_camera_movements(self, scenes: List[dict]) -> List[CameraDecision]:
        """Plan camera movements for each scene"""
        movements = []
        
        for i, scene in enumerate(scenes):
            emotion = scene.get("emotion", "neutral").lower()
            narration = scene.get("narration", "")
            
            # Decide camera movement based on emotion and content
            if emotion == "epic":
                movement = CameraStyle.AERIAL if i == 0 else CameraStyle.DOLLY_IN
            elif emotion == "calm":
                movement = CameraStyle.STATIC if i % 2 == 0 else CameraStyle.ZOOM_SLOW
            elif emotion == "intense":
                movement = CameraStyle.HANDHELD
            elif emotion == "mysterious":
                movement = CameraStyle.DOLLY_IN
            elif emotion == "emotional":
                movement = CameraStyle.ZOOM_SLOW
            else:
                movement = CameraStyle.STATIC
            
            # Check for movement keywords
            if any(word in narration.lower() for word in ["journey", "travel", "across"]):
                movement = CameraStyle.TRACKING
            elif any(word in narration.lower() for word in ["rise", "above", "sky"]):
                movement = CameraStyle.AERIAL
            elif any(word in narration.lower() for word in ["reveal", "appear", "emerge"]):
                movement = CameraStyle.DOLLY_OUT
            
            movements.append(CameraDecision(
                scene_index=i,
                movement=movement,
                speed=1.0 if emotion not in ["calm", "emotional"] else 0.5,
                reasoning=f"Scene {i+1}: {emotion} mood"
            ))
        
        return movements
    
    def _create_music_map(
        self,
        script: str,
        scenes: Optional[List[dict]],
        pacing: PacingDecision
    ) -> List[MusicCue]:
        """Create music timing cues"""
        cues = []
        
        # Estimate video duration
        if scenes:
            total_duration = sum(s.get("duration", pacing.avg_shot_length) for s in scenes)
        else:
            # Rough estimate: 150 words per minute
            words = len(script.split())
            total_duration = (words / 150) * 60
        
        # Opening fade in
        cues.append(MusicCue(
            timestamp=0.0,
            action="fade_in",
            intensity=0.3,
            description="Gentle music entrance"
        ))
        
        # Build at 25%
        cues.append(MusicCue(
            timestamp=total_duration * 0.25,
            action="build",
            intensity=0.5,
            description="Energy starts building"
        ))
        
        # Peak at 60-70%
        cues.append(MusicCue(
            timestamp=total_duration * 0.65,
            action="peak",
            intensity=1.0,
            description="Musical climax"
        ))
        
        # Emotional drop at 75%
        cues.append(MusicCue(
            timestamp=total_duration * 0.75,
            action="drop",
            intensity=0.4,
            description="Reflective moment"
        ))
        
        # Final build to end
        cues.append(MusicCue(
            timestamp=total_duration * 0.90,
            action="build",
            intensity=0.8,
            description="Final emotional swell"
        ))
        
        # Fade out
        cues.append(MusicCue(
            timestamp=total_duration - 2.0,
            action="fade_out",
            intensity=0.0,
            description="Graceful ending"
        ))
        
        return cues
    
    def _map_emotional_arc(
        self,
        script: str,
        scenes: Optional[List[dict]]
    ) -> List[EmotionalBeat]:
        """Map the emotional journey of the video"""
        beats = []
        
        if scenes:
            timestamp = 0.0
            for i, scene in enumerate(scenes):
                emotion = scene.get("emotion", "neutral")
                duration = scene.get("duration", 5.0)
                
                # Calculate intensity based on position (build toward climax)
                position = i / len(scenes)
                if position < 0.3:
                    intensity = 0.3 + position
                elif position < 0.7:
                    intensity = 0.6 + (position - 0.3) * 1.5
                else:
                    intensity = 1.0 - (position - 0.7)
                
                beats.append(EmotionalBeat(
                    timestamp=timestamp,
                    emotion=emotion,
                    intensity=min(intensity, 1.0),
                    description=scene.get("narration", "")[:50]
                ))
                
                timestamp += duration
        
        return beats
    
    def _suggest_visual_metaphors(self, script: str, emotion: str) -> List[Dict[str, str]]:
        """Suggest symbolic imagery based on content"""
        metaphors = []
        script_lower = script.lower()
        
        # Time-related metaphors
        if any(word in script_lower for word in ["time", "history", "past", "future"]):
            metaphors.append({
                "concept": "Time",
                "visual": "Hourglass with golden sand flowing",
                "meaning": "The passage of time and its value"
            })
        
        # Power/strength metaphors
        if any(word in script_lower for word in ["power", "strength", "mighty", "force"]):
            metaphors.append({
                "concept": "Power",
                "visual": "Storm clouds with lightning",
                "meaning": "Raw untamed power"
            })
        
        # Journey metaphors
        if any(word in script_lower for word in ["journey", "path", "road", "travel"]):
            metaphors.append({
                "concept": "Journey",
                "visual": "Winding path through diverse landscapes",
                "meaning": "Life's journey through challenges"
            })
        
        # Transformation metaphors
        if any(word in script_lower for word in ["change", "transform", "evolve", "become"]):
            metaphors.append({
                "concept": "Transformation",
                "visual": "Butterfly emerging from chrysalis",
                "meaning": "Beautiful transformation through struggle"
            })
        
        # Knowledge metaphors
        if any(word in script_lower for word in ["knowledge", "wisdom", "learn", "discover"]):
            metaphors.append({
                "concept": "Knowledge",
                "visual": "Ancient library with glowing books",
                "meaning": "The illuminating power of knowledge"
            })
        
        return metaphors[:3]  # Return top 3
    
    def _determine_overall_style(self, emotion: str, pacing: PacingDecision) -> str:
        """Determine the overall cinematic style"""
        style_map = {
            ("epic", PacingStyle.BUILDING): "Epic Documentary",
            ("epic", PacingStyle.FAST): "Action Epic",
            ("calm", PacingStyle.SLOW): "Meditative Journey",
            ("mysterious", PacingStyle.VARIED): "Noir Thriller",
            ("intense", PacingStyle.FAST): "High-Octane Action",
            ("emotional", PacingStyle.SLOW): "Intimate Drama",
            ("uplifting", PacingStyle.BUILDING): "Inspirational Story",
            ("dark", PacingStyle.VARIED): "Psychological Thriller"
        }
        
        return style_map.get((emotion, pacing.rhythm), "Cinematic Narrative")
    
    def to_generation_config(self, vision: DirectorVision) -> Dict[str, Any]:
        """Convert director vision to video generation config"""
        return {
            "style": vision.overall_style,
            "pacing": {
                "rhythm": vision.pacing.rhythm.value,
                "shot_length": vision.pacing.avg_shot_length
            },
            "colors": {
                "primary": vision.color_palette.primary,
                "secondary": vision.color_palette.secondary,
                "accent": vision.color_palette.accent,
                "lut": vision.color_palette.lut_suggestion
            },
            "music": [
                {"time": cue.timestamp, "action": cue.action, "intensity": cue.intensity}
                for cue in vision.music_map
            ],
            "cameras": [
                {"scene": cam.scene_index, "movement": cam.movement.value, "speed": cam.speed}
                for cam in vision.camera_movements
            ]
        }


# Convenience function
async def direct_video(script: str, scenes: Optional[List[dict]] = None) -> DirectorVision:
    """Quick directorial analysis of a script"""
    director = AIDirector()
    return await director.analyze_script(script, scenes)
