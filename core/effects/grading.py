"""
Color Grading Effects
Emotion-based color grading for video frames.
"""
import numpy as np
from PIL import Image, ImageEnhance
from typing import Dict, Tuple

from ..models import Emotion, ColorPalette


def get_grading_params(emotion: Emotion) -> Dict[str, float]:
    """Get color grading parameters for an emotion."""
    params = {
        Emotion.CALM: {"contrast": 0.95, "saturation": 0.9, "brightness": 1.05},
        Emotion.INTENSE: {"contrast": 1.25, "saturation": 1.3, "brightness": 0.95},
        Emotion.MYSTERIOUS: {"contrast": 1.15, "saturation": 0.7, "brightness": 0.85},
        Emotion.UPLIFTING: {"contrast": 1.05, "saturation": 1.1, "brightness": 1.1},
        Emotion.EPIC: {"contrast": 1.15, "saturation": 1.15, "brightness": 1.0},
        Emotion.SUSPENSE: {"contrast": 1.2, "saturation": 0.8, "brightness": 0.9},
        Emotion.JOY: {"contrast": 1.0, "saturation": 1.2, "brightness": 1.15},
        Emotion.MELANCHOLY: {"contrast": 0.9, "saturation": 0.75, "brightness": 0.9},
        Emotion.NEUTRAL: {"contrast": 1.0, "saturation": 1.0, "brightness": 1.0},
    }
    return params.get(emotion, params[Emotion.NEUTRAL])


def grade_image_by_emotion(
    img: Image.Image, 
    emotion: Emotion,
    palette: Dict[str, Tuple[int, int, int]] = None
) -> Image.Image:
    """
    Apply color grading based on emotional tone.
    
    Args:
        img: Source PIL Image
        emotion: The emotional tone to apply
        palette: Optional color palette override
        
    Returns:
        Graded PIL Image
    """
    params = get_grading_params(emotion)
    
    # Apply contrast
    if params["contrast"] != 1.0:
        img = ImageEnhance.Contrast(img).enhance(params["contrast"])
    
    # Apply saturation
    if params["saturation"] != 1.0:
        img = ImageEnhance.Color(img).enhance(params["saturation"])
    
    # Apply brightness
    if params["brightness"] != 1.0:
        img = ImageEnhance.Brightness(img).enhance(params["brightness"])
    
    # Emotion-specific color shifts
    if emotion == Emotion.MYSTERIOUS:
        # Add blue tint
        arr = np.array(img).astype(float)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.15, 0, 255)  # Boost blue
        img = Image.fromarray(arr.astype(np.uint8))
        
    elif emotion == Emotion.UPLIFTING:
        # Add warm tint
        arr = np.array(img).astype(float)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08, 0, 255)  # Boost red
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05, 0, 255)  # Boost green
        img = Image.fromarray(arr.astype(np.uint8))
        
    elif emotion == Emotion.SUSPENSE:
        # Add cold tint
        arr = np.array(img).astype(float)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.9, 0, 255)   # Reduce red
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.1, 0, 255)   # Boost blue
        img = Image.fromarray(arr.astype(np.uint8))
        
    elif emotion == Emotion.JOY:
        # Add vibrant warm tint
        arr = np.array(img).astype(float)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.05, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.08, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    
    return img


def apply_lut(img: Image.Image, lut_name: str) -> Image.Image:
    """
    Apply a LUT (Look-Up Table) for color grading.
    
    Args:
        img: Source image
        lut_name: Name of the LUT preset
        
    Returns:
        Color-graded image
    """
    # Simplified LUT presets (in practice, would load .cube files)
    presets = {
        "cinematic": {"contrast": 1.1, "saturation": 0.95, "r": 1.0, "g": 0.98, "b": 1.05},
        "teal_orange": {"contrast": 1.15, "saturation": 1.1, "r": 1.1, "g": 0.9, "b": 1.15},
        "vintage": {"contrast": 0.9, "saturation": 0.8, "r": 1.05, "g": 1.0, "b": 0.9},
        "noir": {"contrast": 1.3, "saturation": 0.0, "r": 1.0, "g": 1.0, "b": 1.0},
    }
    
    preset = presets.get(lut_name, presets["cinematic"])
    
    # Apply contrast and saturation
    img = ImageEnhance.Contrast(img).enhance(preset["contrast"])
    img = ImageEnhance.Color(img).enhance(preset["saturation"])
    
    # Apply color channel adjustments
    arr = np.array(img).astype(float)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * preset["r"], 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] * preset["g"], 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * preset["b"], 0, 255)
    
    return Image.fromarray(arr.astype(np.uint8))


def add_film_grain(img: Image.Image, intensity: float = 0.02) -> Image.Image:
    """
    Add subtle film grain for cinematic look.
    
    Args:
        img: Source image
        intensity: Grain intensity (0.0-0.1 recommended)
        
    Returns:
        Image with film grain
    """
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity * 255, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def add_vignette(img: Image.Image, strength: float = 0.3) -> Image.Image:
    """
    Add vignette effect (darkened corners).
    
    Args:
        img: Source image
        strength: Vignette strength (0.0-1.0)
        
    Returns:
        Image with vignette
    """
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]
    
    # Create radial gradient
    y, x = np.ogrid[:h, :w]
    center_x, center_y = w / 2, h / 2
    
    # Normalize distances
    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    dist = dist / max_dist
    
    # Apply vignette
    vignette = 1 - (dist * strength)
    vignette = np.clip(vignette, 0, 1)
    
    # Apply to all channels
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * vignette
    
    return Image.fromarray(arr.astype(np.uint8))
