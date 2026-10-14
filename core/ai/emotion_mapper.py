"""
Emotion Mapper
Maps emotional tones to visual styles, color palettes, and audio characteristics.
"""
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

from ..models import Emotion, ColorPalette, CameraMove

log = logging.getLogger("core.ai.emotion_mapper")


@dataclass
class StyleConfig:
    """Visual style configuration derived from emotion."""
    palette: ColorPalette
    lighting: str  # Description for image generation
    contrast: float  # 0.8 to 1.3
    saturation: float  # 0.7 to 1.3
    brightness: float  # 0.8 to 1.2
    camera_moves: list  # Preferred camera movements
    music_style: str
    pacing: str  # "slow", "medium", "fast"
    transition: str  # "fade", "cut", "dissolve"


# Emotion to style mapping
EMOTION_STYLES: Dict[Emotion, StyleConfig] = {
    Emotion.CALM: StyleConfig(
        palette=ColorPalette.EARTHY,
        lighting="soft ethereal lighting, pastel tones, peaceful atmosphere, gentle bokeh",
        contrast=0.95,
        saturation=0.9,
        brightness=1.05,
        camera_moves=[CameraMove.DOLLY_OUT, CameraMove.PAN_LEFT, CameraMove.STATIC],
        music_style="ambient, soft piano, gentle strings",
        pacing="slow",
        transition="dissolve"
    ),
    Emotion.INTENSE: StyleConfig(
        palette=ColorPalette.NEON,
        lighting="dramatic chiaroscuro, high contrast, saturated colors, dynamic angles",
        contrast=1.25,
        saturation=1.3,
        brightness=0.95,
        camera_moves=[CameraMove.DOLLY_IN, CameraMove.DUTCH_ANGLE, CameraMove.ORBIT],
        music_style="driving beats, electronic, powerful bass",
        pacing="fast",
        transition="cut"
    ),
    Emotion.MYSTERIOUS: StyleConfig(
        palette=ColorPalette.NOIR,
        lighting="moody fog, rim lighting, desaturated tones, film noir aesthetic",
        contrast=1.15,
        saturation=0.7,
        brightness=0.85,
        camera_moves=[CameraMove.PARALLAX, CameraMove.CRANE_UP, CameraMove.PAN_RIGHT],
        music_style="suspenseful, dark ambient, subtle tension",
        pacing="medium",
        transition="fade"
    ),
    Emotion.UPLIFTING: StyleConfig(
        palette=ColorPalette.BLOCKBUSTER,
        lighting="golden hour lighting, warm tones, sun flares, inspirational composition",
        contrast=1.05,
        saturation=1.1,
        brightness=1.1,
        camera_moves=[CameraMove.CRANE_UP, CameraMove.DOLLY_OUT, CameraMove.ORBIT],
        music_style="upbeat, inspiring orchestra, triumphant",
        pacing="medium",
        transition="dissolve"
    ),
    Emotion.EPIC: StyleConfig(
        palette=ColorPalette.BLOCKBUSTER,
        lighting="cinematic wide angle, dramatic clouds, heroic lighting, IMAX quality",
        contrast=1.15,
        saturation=1.15,
        brightness=1.0,
        camera_moves=[CameraMove.DOLLY_IN, CameraMove.CRANE_DOWN, CameraMove.PARALLAX],
        music_style="epic orchestral, powerful drums, soaring strings",
        pacing="medium",
        transition="cut"
    ),
    Emotion.SUSPENSE: StyleConfig(
        palette=ColorPalette.NOIR,
        lighting="low key lighting, deep shadows, cold tones, tense atmosphere",
        contrast=1.2,
        saturation=0.8,
        brightness=0.9,
        camera_moves=[CameraMove.DOLLY_IN, CameraMove.DUTCH_ANGLE, CameraMove.STATIC],
        music_style="tense strings, heartbeat bass, building dread",
        pacing="slow",
        transition="fade"
    ),
    Emotion.JOY: StyleConfig(
        palette=ColorPalette.BLOCKBUSTER,
        lighting="bright natural light, vibrant colors, cheerful atmosphere",
        contrast=1.0,
        saturation=1.2,
        brightness=1.15,
        camera_moves=[CameraMove.ORBIT, CameraMove.DOLLY_OUT, CameraMove.CRANE_UP],
        music_style="happy, upbeat pop, playful melodies",
        pacing="fast",
        transition="cut"
    ),
    Emotion.MELANCHOLY: StyleConfig(
        palette=ColorPalette.EARTHY,
        lighting="overcast soft light, muted tones, nostalgic atmosphere",
        contrast=0.9,
        saturation=0.75,
        brightness=0.9,
        camera_moves=[CameraMove.DOLLY_OUT, CameraMove.PAN_LEFT, CameraMove.STATIC],
        music_style="melancholic piano, slow strings, emotional",
        pacing="slow",
        transition="dissolve"
    ),
    Emotion.NEUTRAL: StyleConfig(
        palette=ColorPalette.MINIMAL,
        lighting="balanced natural lighting, clean professional look",
        contrast=1.0,
        saturation=1.0,
        brightness=1.0,
        camera_moves=[CameraMove.DOLLY_IN, CameraMove.PAN_RIGHT, CameraMove.STATIC],
        music_style="corporate, neutral background, subtle",
        pacing="medium",
        transition="fade"
    )
}


class EmotionMapper:
    """
    Maps emotions to visual and audio styles.
    The creative intelligence that translates feeling into aesthetics.
    """
    
    def __init__(self):
        self.styles = EMOTION_STYLES
    
    def get_style(self, emotion: Emotion) -> StyleConfig:
        """Get the style configuration for an emotion."""
        return self.styles.get(emotion, self.styles[Emotion.NEUTRAL])
    
    def get_palette(self, emotion: Emotion) -> ColorPalette:
        """Get the color palette for an emotion."""
        return self.get_style(emotion).palette
    
    def get_palette_colors(self, emotion: Emotion) -> Dict[str, Tuple[int, int, int]]:
        """Get the actual RGB colors for an emotion's palette."""
        palette = self.get_palette(emotion)
        return palette.value
    
    def enhance_visual_prompt(self, base_prompt: str, emotion: Emotion) -> str:
        """
        Enhance a visual prompt with ultra-detailed cinematic styling.
        Uses film-grade descriptions for Hollywood-quality image generation.
        """
        style = self.get_style(emotion)
        palette = style.palette.value
        
        # Cinematic lens and camera specifications per emotion
        camera_specs = {
            Emotion.CALM: "50mm anamorphic lens, shallow depth of field, f/1.8, dreamy bokeh",
            Emotion.INTENSE: "24mm wide angle, deep focus, f/8, dynamic perspective distortion",
            Emotion.MYSTERIOUS: "85mm telephoto, compressed perspective, f/2.8, film noir shadows",
            Emotion.UPLIFTING: "35mm lens, golden hour backlight, lens flare, f/4",
            Emotion.EPIC: "14mm ultra-wide, IMAX format, infinite depth of field, heroic low angle",
            Emotion.SUSPENSE: "50mm, rack focus ready, f/2, isolating subject from darkness",
            Emotion.JOY: "28mm, natural light, f/5.6, vibrant and sharp",
            Emotion.MELANCHOLY: "85mm, overcast diffusion, f/2.8, intimate and soft",
            Emotion.NEUTRAL: "50mm standard, balanced exposure, f/4, clean and professional"
        }
        
        # Film director/DP style references
        style_references = {
            Emotion.CALM: "Emmanuel Lubezki naturalistic lighting, Terrence Malick poetry",
            Emotion.INTENSE: "Michael Bay dynamic framing, high octane visual energy",
            Emotion.MYSTERIOUS: "Roger Deakins masterful shadows, Denis Villeneuve atmosphere",
            Emotion.UPLIFTING: "Janusz Kamiński golden warmth, Steven Spielberg wonder",
            Emotion.EPIC: "Hoyte van Hoytema IMAX grandeur, Christopher Nolan scale",
            Emotion.SUSPENSE: "Bradford Young dark elegance, David Fincher precision",
            Emotion.JOY: "Robert Richardson vibrant palette, celebration of color",
            Emotion.MELANCHOLY: "Vittorio Storaro painterly composition, emotional depth",
            Emotion.NEUTRAL: "Professional commercial cinematography, clean execution"
        }
        
        # Composition and framing rules
        composition_rules = {
            Emotion.CALM: "rule of thirds, negative space, leading lines to horizon",
            Emotion.INTENSE: "dutch angle allowed, diagonal tension, fill the frame",
            Emotion.MYSTERIOUS: "silhouettes, partial reveals, layered depth",
            Emotion.UPLIFTING: "center-weighted heroic, upward angles, expansive framing",
            Emotion.EPIC: "dramatic leading lines, symmetry, monumental scale",
            Emotion.SUSPENSE: "tight framing, claustrophobic negative space, eye-level",
            Emotion.JOY: "dynamic symmetry, balanced composition, inclusive framing",
            Emotion.MELANCHOLY: "off-center subject, empty space emphasis, contemplative",
            Emotion.NEUTRAL: "classic rule of thirds, balanced professional composition"
        }
        
        camera = camera_specs.get(emotion, camera_specs[Emotion.NEUTRAL])
        reference = style_references.get(emotion, style_references[Emotion.NEUTRAL])
        composition = composition_rules.get(emotion, composition_rules[Emotion.NEUTRAL])
        
        # Build the ultra-detailed cinematic prompt
        cinematic_prompt = f"""CINEMATIC MASTERPIECE, IMAX QUALITY, 9:16 VERTICAL FORMAT

SCENE: {base_prompt}

CAMERA & LENS: {camera}
LIGHTING: {style.lighting}
COMPOSITION: {composition}

VISUAL STYLE: {reference}
Color palette inspired by: warm tones RGB{palette['primary']}, cool accents RGB{palette['secondary']}, highlights RGB{palette['accent']}

TECHNICAL REQUIREMENTS:
- Ultra-sharp focus on subject with cinematic depth falloff
- Volumetric lighting with atmospheric haze
- Ray-traced reflections and realistic shadows
- 8K resolution detail, hyper-realistic textures
- Film grain texture for organic cinematic feel
- Anamorphic lens characteristics (oval bokeh, subtle flares)

MOOD: {emotion.value.upper()} - emotionally evocative, visually stunning

CRITICAL: Photorealistic with artistic stylization. NO text, NO watermarks, NO borders.
Pure visual storytelling suitable for professional film production."""

        return cinematic_prompt
    
    def get_grading_params(self, emotion: Emotion) -> Dict[str, float]:
        """
        Get color grading parameters for post-processing.
        """
        style = self.get_style(emotion)
        return {
            "contrast": style.contrast,
            "saturation": style.saturation,
            "brightness": style.brightness
        }
    
    def suggest_camera_move(self, emotion: Emotion) -> CameraMove:
        """Suggest an appropriate camera movement for the emotion."""
        import random
        style = self.get_style(emotion)
        return random.choice(style.camera_moves)
    
    def get_music_style(self, emotion: Emotion) -> str:
        """Get the music style description for the emotion."""
        return self.get_style(emotion).music_style
    
    def get_pacing(self, emotion: Emotion) -> str:
        """Get the pacing recommendation for the emotion."""
        return self.get_style(emotion).pacing
    
    def get_transition(self, emotion: Emotion) -> str:
        """Get the preferred transition type for the emotion."""
        return self.get_style(emotion).transition
    
    def blend_emotions(
        self, 
        emotion_a: Emotion, 
        emotion_b: Emotion, 
        blend: float = 0.5
    ) -> Dict[str, float]:
        """
        Blend grading parameters between two emotions.
        Useful for transitions between scenes.
        """
        params_a = self.get_grading_params(emotion_a)
        params_b = self.get_grading_params(emotion_b)
        
        return {
            key: params_a[key] * (1 - blend) + params_b[key] * blend
            for key in params_a
        }
