"""
Cinematic Transitions
Premium transition effects between video scenes.
"""
import math
import numpy as np
from typing import Callable, Tuple, Optional
from PIL import Image, ImageFilter

from ..utils.helpers import ease_out_cubic, ease_in_out_cubic, lerp


def crossfade_transition(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    progress: float,
    motion_blur: bool = True
) -> np.ndarray:
    """
    Smooth crossfade with optional motion blur.
    
    Args:
        frame_a: Outgoing frame (HxWx3 uint8)
        frame_b: Incoming frame (HxWx3 uint8)
        progress: Transition progress (0.0 to 1.0)
        motion_blur: Apply subtle motion blur during transition
        
    Returns:
        Blended frame
    """
    eased = ease_in_out_cubic(progress)
    
    blended = (frame_a.astype(np.float32) * (1 - eased) + 
               frame_b.astype(np.float32) * eased)
    
    if motion_blur and 0.2 < progress < 0.8:
        # Apply subtle blur in the middle of transition
        blur_strength = 1 - abs(progress - 0.5) * 2
        if blur_strength > 0.3:
            img = Image.fromarray(blended.astype(np.uint8))
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_strength * 2))
            blended = np.array(img).astype(np.float32)
    
    return np.clip(blended, 0, 255).astype(np.uint8)


def zoom_transition(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    progress: float,
    zoom_out: bool = False
) -> np.ndarray:
    """
    Zoom in/out transition.
    
    Args:
        frame_a: Outgoing frame
        frame_b: Incoming frame
        progress: Transition progress (0.0 to 1.0)
        zoom_out: If True, zoom out; otherwise zoom in
        
    Returns:
        Transitioned frame
    """
    eased = ease_in_out_cubic(progress)
    h, w = frame_a.shape[:2]
    
    if progress < 0.5:
        # First half: zoom the outgoing frame
        frame = frame_a
        local_progress = eased * 2  # 0 to 1 in first half
        if zoom_out:
            scale = lerp(1.0, 0.7, local_progress)
        else:
            scale = lerp(1.0, 1.5, local_progress)
        alpha = 1.0 - local_progress
    else:
        # Second half: reveal incoming frame
        frame = frame_b
        local_progress = (eased - 0.5) * 2  # 0 to 1 in second half
        if zoom_out:
            scale = lerp(1.5, 1.0, local_progress)
        else:
            scale = lerp(0.7, 1.0, local_progress)
        alpha = local_progress
    
    # Apply scale
    img = Image.fromarray(frame)
    new_size = (int(w * scale), int(h * scale))
    img_scaled = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Center crop/pad
    result = Image.new("RGB", (w, h), (0, 0, 0))
    paste_x = (w - new_size[0]) // 2
    paste_y = (h - new_size[1]) // 2
    
    if scale >= 1.0:
        # Crop
        crop_x = (new_size[0] - w) // 2
        crop_y = (new_size[1] - h) // 2
        img_scaled = img_scaled.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        result = img_scaled
    else:
        # Pad with black
        result.paste(img_scaled, (paste_x, paste_y))
    
    # Blend for smooth transition at midpoint
    if 0.4 < progress < 0.6:
        blend = (progress - 0.4) / 0.2
        result_arr = np.array(result).astype(np.float32)
        other = frame_b if progress < 0.5 else frame_a
        result_arr = result_arr * (1 - blend * 0.5) + other.astype(np.float32) * (blend * 0.5)
        return np.clip(result_arr, 0, 255).astype(np.uint8)
    
    return np.array(result)


def wipe_transition(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    progress: float,
    direction: str = "left"
) -> np.ndarray:
    """
    Wipe transition (reveal incoming frame from one side).
    
    Args:
        frame_a: Outgoing frame
        frame_b: Incoming frame
        progress: Transition progress (0.0 to 1.0)
        direction: 'left', 'right', 'up', 'down'
        
    Returns:
        Transitioned frame
    """
    eased = ease_in_out_cubic(progress)
    h, w = frame_a.shape[:2]
    result = frame_a.copy()
    
    if direction == "left":
        split = int(w * eased)
        result[:, :split] = frame_b[:, :split]
    elif direction == "right":
        split = int(w * (1 - eased))
        result[:, split:] = frame_b[:, split:]
    elif direction == "up":
        split = int(h * eased)
        result[:split, :] = frame_b[:split, :]
    elif direction == "down":
        split = int(h * (1 - eased))
        result[split:, :] = frame_b[split:, :]
    
    # Soft edge
    edge_width = 20
    if direction in ["left", "right"]:
        x = int(w * eased) if direction == "left" else int(w * (1 - eased))
        for i in range(edge_width):
            if direction == "left":
                col = min(x + i, w - 1)
            else:
                col = max(x - i, 0)
            blend = i / edge_width
            result[:, col] = (
                frame_a[:, col].astype(np.float32) * blend +
                frame_b[:, col].astype(np.float32) * (1 - blend)
            ).astype(np.uint8)
    
    return result


def light_wipe_transition(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    progress: float
) -> np.ndarray:
    """
    Cinematic light wipe (bright flash reveals new scene).
    
    Args:
        frame_a: Outgoing frame
        frame_b: Incoming frame
        progress: Transition progress (0.0 to 1.0)
        
    Returns:
        Transitioned frame
    """
    eased = ease_in_out_cubic(progress)
    h, w = frame_a.shape[:2]
    
    # Calculate brightness boost for the "flash"
    if progress < 0.3:
        # Fade to white
        brightness = (progress / 0.3) ** 2
        base = frame_a
    elif progress < 0.5:
        # Hold white
        brightness = 1.0
        base = frame_a
    else:
        # Fade from white to new scene
        brightness = ((1 - progress) / 0.5) ** 2
        base = frame_b
    
    # Apply brightness boost
    result = base.astype(np.float32)
    white = np.ones_like(result) * 255
    result = result * (1 - brightness) + white * brightness
    
    # Blend frames near midpoint
    if 0.45 < progress < 0.55:
        blend = (progress - 0.45) / 0.1
        result = (frame_a.astype(np.float32) * (1 - blend) + 
                  frame_b.astype(np.float32) * blend)
        result = result * (1 - brightness * 0.5) + white * (brightness * 0.5)
    
    return np.clip(result, 0, 255).astype(np.uint8)


def push_transition(
    frame_a: np.ndarray,
    frame_b: np.ndarray,
    progress: float,
    direction: str = "left"
) -> np.ndarray:
    """
    Push transition (new frame pushes old frame off screen).
    
    Args:
        frame_a: Outgoing frame
        frame_b: Incoming frame
        progress: Transition progress (0.0 to 1.0)
        direction: 'left', 'right', 'up', 'down'
        
    Returns:
        Transitioned frame
    """
    eased = ease_out_cubic(progress)
    h, w = frame_a.shape[:2]
    result = np.zeros_like(frame_a)
    
    if direction == "left":
        offset = int(w * eased)
        if offset < w:
            result[:, :w-offset] = frame_a[:, offset:]
        if offset > 0:
            result[:, w-offset:] = frame_b[:, :offset]
    elif direction == "right":
        offset = int(w * eased)
        if offset < w:
            result[:, offset:] = frame_a[:, :w-offset]
        if offset > 0:
            result[:, :offset] = frame_b[:, w-offset:]
    elif direction == "up":
        offset = int(h * eased)
        if offset < h:
            result[:h-offset, :] = frame_a[offset:, :]
        if offset > 0:
            result[h-offset:, :] = frame_b[:offset, :]
    elif direction == "down":
        offset = int(h * eased)
        if offset < h:
            result[offset:, :] = frame_a[:h-offset, :]
        if offset > 0:
            result[:offset, :] = frame_b[h-offset:, :]
    
    return result


class TransitionManager:
    """
    Manages transitions between video scenes.
    """
    
    TRANSITION_TYPES = {
        "crossfade": crossfade_transition,
        "dissolve": crossfade_transition,
        "fade": crossfade_transition,
        "zoom": zoom_transition,
        "zoom_in": lambda a, b, p: zoom_transition(a, b, p, zoom_out=False),
        "zoom_out": lambda a, b, p: zoom_transition(a, b, p, zoom_out=True),
        "wipe_left": lambda a, b, p: wipe_transition(a, b, p, direction="left"),
        "wipe_right": lambda a, b, p: wipe_transition(a, b, p, direction="right"),
        "wipe_up": lambda a, b, p: wipe_transition(a, b, p, direction="up"),
        "wipe_down": lambda a, b, p: wipe_transition(a, b, p, direction="down"),
        "light_wipe": light_wipe_transition,
        "push_left": lambda a, b, p: push_transition(a, b, p, direction="left"),
        "push_right": lambda a, b, p: push_transition(a, b, p, direction="right"),
        "cut": lambda a, b, p: b if p > 0.5 else a,
    }
    
    def __init__(self, default_duration: float = 0.5):
        """
        Initialize transition manager.
        
        Args:
            default_duration: Default transition duration in seconds
        """
        self.default_duration = default_duration
    
    def get_transition(self, transition_type: str) -> Callable:
        """Get transition function by name."""
        return self.TRANSITION_TYPES.get(
            transition_type, 
            self.TRANSITION_TYPES["crossfade"]
        )
    
    def apply_transition(
        self,
        frame_a: np.ndarray,
        frame_b: np.ndarray,
        progress: float,
        transition_type: str = "crossfade"
    ) -> np.ndarray:
        """
        Apply a transition between two frames.
        
        Args:
            frame_a: Outgoing frame
            frame_b: Incoming frame
            progress: Transition progress (0.0 to 1.0)
            transition_type: Name of transition to apply
            
        Returns:
            Transitioned frame
        """
        transition_fn = self.get_transition(transition_type)
        return transition_fn(frame_a, frame_b, progress)
    
    def suggest_transition(self, from_emotion: str, to_emotion: str) -> str:
        """
        Suggest an appropriate transition based on emotional shift.
        
        Args:
            from_emotion: Current scene emotion
            to_emotion: Next scene emotion
            
        Returns:
            Recommended transition type
        """
        calm_emotions = {"calm", "neutral", "melancholy", "peaceful"}
        intense_emotions = {"intense", "epic", "suspense", "action"}
        uplifting_emotions = {"uplifting", "joy", "inspiring"}
        
        from_e = from_emotion.lower()
        to_e = to_emotion.lower()
        
        # Intense to calm: slow dissolve
        if from_e in intense_emotions and to_e in calm_emotions:
            return "dissolve"
        
        # Calm to intense: quick cut or zoom
        if from_e in calm_emotions and to_e in intense_emotions:
            return "zoom_in"
        
        # Building intensity: push
        if from_e in calm_emotions and to_e in uplifting_emotions:
            return "push_left"
        
        # Mystery/suspense: light wipe
        if to_e in {"mysterious", "suspense"}:
            return "light_wipe"
        
        # Same emotion: crossfade
        if from_e == to_e:
            return "crossfade"
        
        # Default
        return "crossfade"
