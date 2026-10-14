"""
Smart Transitions Engine for MAK AI
Emotion-aware transition selection between video scenes.

Features:
- Automatic transition selection based on emotional context
- 20+ cinematic transition effects
- Audio-synced transitions with sound effects
- Platform-optimized (TikTok, YouTube Shorts, Reels)
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List, Callable
from pathlib import Path

log = logging.getLogger("smart_transitions")


class Emotion(Enum):
    """Scene emotions for transition decisions"""
    CALM = "calm"
    INTENSE = "intense"
    EPIC = "epic"
    MYSTERIOUS = "mysterious"
    EMOTIONAL = "emotional"
    UPLIFTING = "uplifting"
    DARK = "dark"
    NEUTRAL = "neutral"
    SUSPENSE = "suspense"
    JOYFUL = "joyful"


class TransitionType(Enum):
    """Available transition types"""
    # Quick cuts
    HARD_CUT = "hard_cut"
    RAPID_CUT = "rapid_cut"
    JUMP_CUT = "jump_cut"
    
    # Fades and dissolves
    FADE_BLACK = "fade_black"
    FADE_WHITE = "fade_white"
    CROSS_DISSOLVE = "cross_dissolve"
    SLOW_DISSOLVE = "slow_dissolve"
    
    # Motion transitions
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ZOOM_BLUR = "zoom_blur"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    
    # Creative transitions
    GLITCH = "glitch"
    SHAKE = "shake"
    FLASH = "flash"
    RIPPLE = "ripple"
    PIXELATE = "pixelate"
    
    # Thematic transitions
    CLOCK_WIPE = "clock_wipe"
    PAGE_TURN = "page_turn"
    INK_SPREAD = "ink_spread"
    LIGHT_LEAK = "light_leak"
    FILM_BURN = "film_burn"
    
    # Sound-synced
    WHOOSH_CUT = "whoosh_cut"
    BASS_DROP = "bass_drop"
    IMPACT_CUT = "impact_cut"


@dataclass
class TransitionConfig:
    """Configuration for a transition effect"""
    type: TransitionType
    duration: float = 0.5  # seconds
    easing: str = "ease_in_out"
    has_sound: bool = False
    sound_file: Optional[str] = None
    intensity: float = 1.0  # 0.0 - 1.0


@dataclass
class TransitionDecision:
    """Result of transition selection"""
    transition: TransitionConfig
    reasoning: str
    alternatives: List[TransitionType]
    audio_cue: Optional[str] = None


class SmartTransitions:
    """
    Intelligent transition selection based on emotional context.
    
    Analyzes the emotional shift between scenes and selects
    the most appropriate cinematic transition.
    """
    
    # Emotion shift to transition mapping
    TRANSITION_RULES = {
        # Calm transitions
        ("calm", "calm"): {
            "primary": TransitionType.CROSS_DISSOLVE,
            "alternatives": [TransitionType.SLOW_DISSOLVE, TransitionType.FADE_BLACK],
            "duration": 1.0,
            "reasoning": "Gentle transition maintains peaceful mood"
        },
        ("calm", "intense"): {
            "primary": TransitionType.WHOOSH_CUT,
            "alternatives": [TransitionType.RAPID_CUT, TransitionType.FLASH],
            "duration": 0.3,
            "sound": "whoosh_rise.mp3",
            "reasoning": "Sharp transition signals energy shift"
        },
        ("calm", "epic"): {
            "primary": TransitionType.ZOOM_IN,
            "alternatives": [TransitionType.BASS_DROP, TransitionType.ZOOM_BLUR],
            "duration": 0.5,
            "sound": "epic_boom.mp3",
            "reasoning": "Building transition crescendos to epic moment"
        },
        ("calm", "mysterious"): {
            "primary": TransitionType.INK_SPREAD,
            "alternatives": [TransitionType.FADE_BLACK, TransitionType.SLOW_DISSOLVE],
            "duration": 0.8,
            "reasoning": "Dark seeping transition builds intrigue"
        },
        
        # Intense transitions
        ("intense", "calm"): {
            "primary": TransitionType.SLOW_DISSOLVE,
            "alternatives": [TransitionType.FADE_WHITE, TransitionType.ZOOM_OUT],
            "duration": 1.2,
            "reasoning": "Gradual release from tension"
        },
        ("intense", "intense"): {
            "primary": TransitionType.RAPID_CUT,
            "alternatives": [TransitionType.JUMP_CUT, TransitionType.SHAKE],
            "duration": 0.1,
            "reasoning": "Rapid cuts maintain high energy"
        },
        ("intense", "epic"): {
            "primary": TransitionType.BASS_DROP,
            "alternatives": [TransitionType.IMPACT_CUT, TransitionType.FLASH],
            "duration": 0.4,
            "sound": "bass_drop.mp3",
            "reasoning": "Explosive transition for climactic moment"
        },
        
        # Epic transitions
        ("epic", "calm"): {
            "primary": TransitionType.FADE_WHITE,
            "alternatives": [TransitionType.SLOW_DISSOLVE, TransitionType.ZOOM_OUT],
            "duration": 1.5,
            "reasoning": "Heavenly fade releases epicness"
        },
        ("epic", "epic"): {
            "primary": TransitionType.IMPACT_CUT,
            "alternatives": [TransitionType.FLASH, TransitionType.WHOOSH_CUT],
            "duration": 0.2,
            "sound": "impact.mp3",
            "reasoning": "Powerful cuts sustain epic feeling"
        },
        ("epic", "emotional"): {
            "primary": TransitionType.LIGHT_LEAK,
            "alternatives": [TransitionType.CROSS_DISSOLVE, TransitionType.FADE_WHITE],
            "duration": 1.0,
            "reasoning": "Warm light transition moves to heart"
        },
        
        # Mysterious transitions
        ("mysterious", "mysterious"): {
            "primary": TransitionType.FADE_BLACK,
            "alternatives": [TransitionType.INK_SPREAD, TransitionType.RIPPLE],
            "duration": 0.8,
            "reasoning": "Dark transitions maintain suspense"
        },
        ("mysterious", "intense"): {
            "primary": TransitionType.GLITCH,
            "alternatives": [TransitionType.FLASH, TransitionType.SHAKE],
            "duration": 0.3,
            "sound": "glitch.mp3",
            "reasoning": "Glitch reveals hidden tension"
        },
        ("mysterious", "epic"): {
            "primary": TransitionType.ZOOM_BLUR,
            "alternatives": [TransitionType.BASS_DROP, TransitionType.FLASH],
            "duration": 0.5,
            "sound": "reveal.mp3",
            "reasoning": "Dramatic reveal of epic truth"
        },
        
        # Emotional transitions
        ("emotional", "emotional"): {
            "primary": TransitionType.CROSS_DISSOLVE,
            "alternatives": [TransitionType.LIGHT_LEAK, TransitionType.SLOW_DISSOLVE],
            "duration": 1.2,
            "reasoning": "Soft blending maintains emotional connection"
        },
        ("emotional", "epic"): {
            "primary": TransitionType.ZOOM_IN,
            "alternatives": [TransitionType.LIGHT_LEAK, TransitionType.FADE_WHITE],
            "duration": 0.6,
            "reasoning": "Emotion builds to triumph"
        },
        ("emotional", "calm"): {
            "primary": TransitionType.SLOW_DISSOLVE,
            "alternatives": [TransitionType.FADE_BLACK, TransitionType.CROSS_DISSOLVE],
            "duration": 1.0,
            "reasoning": "Gentle release from emotional moment"
        },
        
        # Narrative transitions (for time/location changes)
        ("time_jump", "any"): {
            "primary": TransitionType.CLOCK_WIPE,
            "alternatives": [TransitionType.FADE_BLACK, TransitionType.GLITCH],
            "duration": 0.8,
            "reasoning": "Visual cue for time passage"
        },
        ("location_change", "any"): {
            "primary": TransitionType.ZOOM_BLUR,
            "alternatives": [TransitionType.SLIDE_LEFT, TransitionType.WHOOSH_CUT],
            "duration": 0.5,
            "sound": "travel_whoosh.mp3",
            "reasoning": "Motion suggests travel/movement"
        },
        ("plot_twist", "any"): {
            "primary": TransitionType.GLITCH,
            "alternatives": [TransitionType.BASS_DROP, TransitionType.SHAKE],
            "duration": 0.3,
            "sound": "bass_drop.mp3",
            "reasoning": "Disorienting effect emphasizes twist"
        },
        
        # Default fallback
        ("neutral", "neutral"): {
            "primary": TransitionType.CROSS_DISSOLVE,
            "alternatives": [TransitionType.HARD_CUT, TransitionType.FADE_BLACK],
            "duration": 0.5,
            "reasoning": "Standard professional transition"
        }
    }
    
    # Sound effects library
    SOUND_EFFECTS = {
        "whoosh_rise.mp3": "assets/sfx/whoosh_rise.mp3",
        "whoosh_fall.mp3": "assets/sfx/whoosh_fall.mp3",
        "bass_drop.mp3": "assets/sfx/bass_drop.mp3",
        "impact.mp3": "assets/sfx/impact.mp3",
        "glitch.mp3": "assets/sfx/glitch.mp3",
        "reveal.mp3": "assets/sfx/reveal.mp3",
        "epic_boom.mp3": "assets/sfx/epic_boom.mp3",
        "travel_whoosh.mp3": "assets/sfx/travel_whoosh.mp3"
    }
    
    def __init__(self, sfx_dir: Optional[Path] = None):
        """Initialize with optional custom SFX directory"""
        self.sfx_dir = sfx_dir or Path("assets/sfx")
        log.info("🎬 Smart Transitions engine initialized")
    
    def analyze_emotional_shift(
        self,
        scene_a: dict,
        scene_b: dict
    ) -> Tuple[str, str, Optional[str]]:
        """
        Detect emotional change between scenes.
        
        Args:
            scene_a: First scene with 'emotion' key
            scene_b: Second scene with 'emotion' key
            
        Returns:
            Tuple of (emotion_a, emotion_b, special_type if any)
        """
        emotion_a = scene_a.get("emotion", "neutral").lower()
        emotion_b = scene_b.get("emotion", "neutral").lower()
        
        # Detect special narrative transitions
        special_type = None
        
        # Check for time jump keywords
        text_b = scene_b.get("narration", "").lower()
        if any(kw in text_b for kw in ["years later", "months later", "the next day", "after", "then"]):
            special_type = "time_jump"
        
        # Check for location change
        if any(kw in text_b for kw in ["meanwhile", "across", "in another", "far away", "elsewhere"]):
            special_type = "location_change"
        
        # Check for plot twist
        if any(kw in text_b for kw in ["but then", "suddenly", "however", "twist", "revealed"]):
            special_type = "plot_twist"
        
        return emotion_a, emotion_b, special_type
    
    def select_transition(
        self,
        scene_a: dict,
        scene_b: dict,
        platform: str = "tiktok"
    ) -> TransitionDecision:
        """
        Select the optimal transition between two scenes.
        
        Args:
            scene_a: First scene data
            scene_b: Second scene data
            platform: Target platform (tiktok, youtube, instagram)
            
        Returns:
            TransitionDecision with selected transition and alternatives
        """
        emotion_a, emotion_b, special_type = self.analyze_emotional_shift(scene_a, scene_b)
        
        # Check for special narrative transition first
        if special_type:
            rule_key = (special_type, "any")
        else:
            rule_key = (emotion_a, emotion_b)
        
        # Get rule, falling back to reverse or neutral
        rule = self.TRANSITION_RULES.get(rule_key)
        if not rule:
            rule = self.TRANSITION_RULES.get((emotion_b, emotion_a))
        if not rule:
            rule = self.TRANSITION_RULES.get(("neutral", "neutral"))
        
        # Adjust duration for platform
        duration = rule.get("duration", 0.5)
        if platform == "tiktok":
            duration = min(duration, 0.5)  # TikTok prefers faster cuts
        elif platform == "youtube":
            duration = duration * 1.2  # YouTube can be slightly slower
        
        # Build transition config
        transition = TransitionConfig(
            type=rule["primary"],
            duration=duration,
            has_sound=bool(rule.get("sound")),
            sound_file=rule.get("sound"),
            intensity=1.0
        )
        
        # Get audio cue if any
        audio_cue = None
        if rule.get("sound"):
            sfx_path = self.sfx_dir / rule["sound"]
            if sfx_path.exists():
                audio_cue = str(sfx_path)
        
        decision = TransitionDecision(
            transition=transition,
            reasoning=rule["reasoning"],
            alternatives=rule.get("alternatives", []),
            audio_cue=audio_cue
        )
        
        log.info(
            f"🎬 Transition: {emotion_a} → {emotion_b} = {rule['primary'].value} "
            f"({decision.reasoning})"
        )
        
        return decision
    
    def get_transition_sequence(
        self,
        scenes: List[dict],
        platform: str = "tiktok"
    ) -> List[TransitionDecision]:
        """
        Generate optimal transitions for an entire video.
        
        Args:
            scenes: List of scene data dictionaries
            platform: Target platform
            
        Returns:
            List of transitions (one less than number of scenes)
        """
        transitions = []
        
        for i in range(len(scenes) - 1):
            decision = self.select_transition(
                scenes[i],
                scenes[i + 1],
                platform
            )
            transitions.append(decision)
        
        return transitions
    
    def apply_transition(
        self,
        clip_a,
        clip_b,
        transition: TransitionConfig
    ):
        """
        Apply a transition effect between two MoviePy clips.
        
        This integrates with MoviePy to create the actual transition.
        """
        from moviepy.editor import CompositeVideoClip, concatenate_videoclips
        
        duration = transition.duration
        
        if transition.type == TransitionType.HARD_CUT:
            # No transition, just concatenate
            return concatenate_videoclips([clip_a, clip_b])
        
        elif transition.type == TransitionType.CROSS_DISSOLVE:
            # Crossfade
            clip_a = clip_a.crossfadeout(duration)
            clip_b = clip_b.crossfadein(duration).set_start(clip_a.duration - duration)
            return CompositeVideoClip([clip_a, clip_b])
        
        elif transition.type == TransitionType.FADE_BLACK:
            # Fade through black
            clip_a = clip_a.fadeout(duration / 2)
            clip_b = clip_b.fadein(duration / 2)
            return concatenate_videoclips([clip_a, clip_b])
        
        elif transition.type == TransitionType.FADE_WHITE:
            # Fade through white
            clip_a = clip_a.fadeout(duration / 2, final_color=[255, 255, 255])
            clip_b = clip_b.fadein(duration / 2, initial_color=[255, 255, 255])
            return concatenate_videoclips([clip_a, clip_b])
        
        elif transition.type == TransitionType.ZOOM_IN:
            # Zoom into center
            end_clip_a = clip_a.subclip(clip_a.duration - duration)
            zoomed = end_clip_a.resize(lambda t: 1 + 0.5 * (t / duration))
            clip_b_delayed = clip_b.set_start(clip_a.duration)
            return CompositeVideoClip([
                clip_a.set_duration(clip_a.duration - duration),
                zoomed.set_start(clip_a.duration - duration),
                clip_b_delayed
            ])
        
        elif transition.type in [TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT]:
            # Slide transition
            direction = 1 if transition.type == TransitionType.SLIDE_LEFT else -1
            
            def slide_out(t):
                progress = t / duration
                return (direction * progress * clip_a.w, 0)
            
            def slide_in(t):
                progress = t / duration
                return (-direction * (1 - progress) * clip_b.w, 0)
            
            clip_a_end = clip_a.subclip(clip_a.duration - duration).set_position(slide_out)
            clip_b_start = clip_b.subclip(0, duration).set_position(slide_in)
            
            # This is a simplified version - full implementation would be more complex
            return concatenate_videoclips([
                clip_a.set_duration(clip_a.duration - duration),
                CompositeVideoClip([clip_a_end, clip_b_start]).set_duration(duration),
                clip_b.subclip(duration)
            ])
        
        else:
            # Default to crossfade for unimplemented transitions
            clip_a = clip_a.crossfadeout(duration)
            clip_b = clip_b.crossfadein(duration).set_start(clip_a.duration - duration)
            return CompositeVideoClip([clip_a, clip_b])
    
    def apply_transition_with_sound(
        self,
        clip_a,
        clip_b,
        decision: TransitionDecision
    ):
        """Apply transition with synchronized sound effect"""
        from moviepy.editor import AudioFileClip, CompositeAudioClip
        
        # Apply visual transition
        result = self.apply_transition(clip_a, clip_b, decision.transition)
        
        # Add sound effect if available
        if decision.audio_cue and Path(decision.audio_cue).exists():
            sfx = AudioFileClip(decision.audio_cue)
            
            # Position sound at transition point
            transition_start = clip_a.duration - decision.transition.duration
            sfx = sfx.set_start(transition_start)
            
            # Mix with existing audio
            if result.audio:
                combined_audio = CompositeAudioClip([result.audio, sfx])
                result = result.set_audio(combined_audio)
            else:
                result = result.set_audio(sfx)
        
        return result


# Convenience functions
def get_smart_transition(scene_a: dict, scene_b: dict) -> TransitionDecision:
    """Quick transition selection between two scenes"""
    engine = SmartTransitions()
    return engine.select_transition(scene_a, scene_b)


def get_all_transitions(scenes: List[dict], platform: str = "tiktok") -> List[TransitionDecision]:
    """Get all transitions for a video sequence"""
    engine = SmartTransitions()
    return engine.get_transition_sequence(scenes, platform)
