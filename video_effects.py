# video_effects.py — Premium Video Effects Module
# Crossfades, light leaks, film grain, zoom transitions, overlays

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from moviepy.editor import VideoClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout
import random
import math

# ══════════════════════════════════════════════════════════════
# TRANSITIONS
# ══════════════════════════════════════════════════════════════

def crossfade_clips(clip1, clip2, duration: float = 0.5):
    """Create smooth crossfade transition between two clips."""
    # Fade out clip1, fade in clip2, overlap them
    clip1 = fadeout(clip1, duration)
    clip2 = fadein(clip2, duration)
    
    # Overlap: clip2 starts before clip1 ends
    clip2 = clip2.set_start(clip1.duration - duration)
    
    return CompositeVideoClip([clip1, clip2])


def zoom_transition(clip1, clip2, duration: float = 0.3):
    """Zoom-in transition effect."""
    # This creates a zoom-in effect at the end of clip1
    # and zoom-out at the start of clip2
    
    def zoom_out_frame(get_frame, t):
        progress = t / duration
        scale = 1.0 + (0.3 * progress)  # Zoom in as we transition
        frame = get_frame(t)
        # Apply zoom effect...
        return frame
    
    # For now, use crossfade (zoom requires more complex PIL work)
    return crossfade_clips(clip1, clip2, duration)


# ══════════════════════════════════════════════════════════════
# OVERLAYS
# ══════════════════════════════════════════════════════════════

def create_light_leak_overlay(width: int, height: int, intensity: float = 0.15):
    """Create a warm light leak overlay effect."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Random warm color leak from corner
    leak_colors = [
        (255, 180, 100),  # Warm orange
        (255, 200, 150),  # Soft peach
        (255, 150, 80),   # Deep orange
        (255, 220, 180),  # Cream
    ]
    color = random.choice(leak_colors)
    
    # Create gradient leak from corner
    corner = random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])
    
    if corner == "top_left":
        cx, cy = 0, 0
    elif corner == "top_right":
        cx, cy = width, 0
    elif corner == "bottom_left":
        cx, cy = 0, height
    else:
        cx, cy = width, height
    
    # Radial gradient
    for i in range(100, 0, -1):
        radius = int((i / 100) * max(width, height) * 0.7)
        alpha = int((100 - i) * 2.5 * intensity)
        alpha = min(255, max(0, alpha))
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(*color, alpha)
        )
    
    # Blur for softness
    img = img.filter(ImageFilter.GaussianBlur(radius=50))
    
    return img


def apply_film_grain(frame: np.ndarray, intensity: float = 0.03) -> np.ndarray:
    """Add subtle film grain to a frame."""
    h, w = frame.shape[:2]
    grain = np.random.normal(0, intensity * 255, (h, w, 1)).astype(np.float32)
    grain = np.repeat(grain, 3, axis=2)
    
    result = frame.astype(np.float32) + grain
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_vignette(frame: np.ndarray, intensity: float = 0.3) -> np.ndarray:
    """Apply vignette (darkened edges) effect."""
    h, w = frame.shape[:2]
    
    # Create vignette mask
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    
    # Distance from center
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt(cx**2 + cy**2)
    
    # Vignette falloff
    vignette = 1 - (dist / max_dist) * intensity
    vignette = np.clip(vignette, 0.5, 1.0)
    
    # Apply to frame
    result = frame.astype(np.float32) * vignette[:, :, np.newaxis]
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_grade(frame: np.ndarray, style: str = "cinematic") -> np.ndarray:
    """Apply cinematic color grading."""
    frame = frame.astype(np.float32)
    
    if style == "cinematic":
        # Teal shadows, orange highlights (blockbuster look)
        frame[:, :, 0] = frame[:, :, 0] * 0.95  # Reduce red in shadows
        frame[:, :, 1] = frame[:, :, 1] * 0.97  # Slight green reduction
        frame[:, :, 2] = frame[:, :, 2] * 1.08  # Boost blue (teal shadows)
        
        # Lift highlights with warmth
        bright = frame.mean(axis=2) > 180
        frame[bright, 0] *= 1.05  # Add red to highlights
        frame[bright, 1] *= 1.02  # Slight warmth
        
    elif style == "warm":
        frame[:, :, 0] *= 1.1   # Boost red
        frame[:, :, 1] *= 1.05  # Boost green
        frame[:, :, 2] *= 0.9   # Reduce blue
        
    elif style == "cool":
        frame[:, :, 0] *= 0.9   # Reduce red
        frame[:, :, 1] *= 0.95  # Reduce green
        frame[:, :, 2] *= 1.1   # Boost blue
    
    return np.clip(frame, 0, 255).astype(np.uint8)


# ══════════════════════════════════════════════════════════════
# CAMERA EFFECTS
# ══════════════════════════════════════════════════════════════

def apply_shake(frame: np.ndarray, t: float, intensity: float = 3.0) -> np.ndarray:
    """Apply subtle camera shake effect."""
    # Use time-based pseudo-random shake
    offset_x = int(math.sin(t * 15) * intensity)
    offset_y = int(math.cos(t * 12) * intensity)
    
    h, w = frame.shape[:2]
    
    # Roll the frame
    result = np.roll(frame, offset_x, axis=1)
    result = np.roll(result, offset_y, axis=0)
    
    return result


def apply_pulse_zoom(scale_base: float, t: float, duration: float, intensity: float = 0.02) -> float:
    """Create subtle breathing/pulse zoom effect."""
    # Subtle sine wave zoom
    pulse = math.sin((t / duration) * math.pi * 4) * intensity
    return scale_base + pulse


# ══════════════════════════════════════════════════════════════
# COMBINED EFFECT PIPELINE
# ══════════════════════════════════════════════════════════════

def apply_all_effects(frame: np.ndarray, t: float, duration: float,
                      grain: bool = True, vignette: bool = True,
                      color_grade: str = "cinematic") -> np.ndarray:
    """Apply full effect pipeline to a frame."""
    
    # Color grading first
    if color_grade:
        frame = apply_color_grade(frame, color_grade)
    
    # Vignette
    if vignette:
        frame = apply_vignette(frame, intensity=0.25)
    
    # Film grain (subtle)
    if grain:
        frame = apply_film_grain(frame, intensity=0.02)
    
    return frame


# ══════════════════════════════════════════════════════════════
# ANIMATED OVERLAYS
# ══════════════════════════════════════════════════════════════

def create_animated_light_leak_clip(width: int, height: int, duration: float):
    """Create an animated light leak overlay clip."""
    
    # Pre-generate light leak frame
    leak_img = create_light_leak_overlay(width, height, intensity=0.2)
    leak_array = np.array(leak_img)
    
    def make_frame(t):
        # Pulsing intensity
        intensity = 0.5 + 0.5 * math.sin(t * 2)
        
        # Apply intensity to alpha
        frame = leak_array.copy()
        frame[:, :, 3] = (frame[:, :, 3] * intensity).astype(np.uint8)
        
        # Convert RGBA to RGB with transparency simulation
        rgb = frame[:, :, :3].astype(np.float32)
        alpha = frame[:, :, 3:4].astype(np.float32) / 255
        
        # Blend with black (will be composited over video)
        result = (rgb * alpha).astype(np.uint8)
        
        return result
    
    return VideoClip(make_frame=make_frame, duration=duration)


def create_particle_overlay(width: int, height: int, duration: float, num_particles: int = 30):
    """Create floating dust particle overlay."""
    
    # Generate particle positions and properties
    particles = []
    for _ in range(num_particles):
        particles.append({
            'x': random.randint(0, width),
            'y': random.randint(0, height),
            'size': random.randint(2, 5),
            'speed_y': random.uniform(-30, -10),  # Float upward
            'speed_x': random.uniform(-5, 5),
            'alpha': random.randint(100, 200),
            'phase': random.uniform(0, 2 * math.pi)
        })
    
    def make_frame(t):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        for p in particles:
            # Calculate position with time
            x = (p['x'] + p['speed_x'] * t + math.sin(t + p['phase']) * 10) % width
            y = (p['y'] + p['speed_y'] * t) % height
            
            # Pulsing alpha
            alpha = int(p['alpha'] * (0.5 + 0.5 * math.sin(t * 2 + p['phase'])))
            
            # Draw particle
            draw.ellipse(
                [x - p['size'], y - p['size'], x + p['size'], y + p['size']],
                fill=(255, 255, 255, alpha)
            )
        
        # Blur for softness
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        return np.array(img)[:, :, :3]  # Return RGB only
    
    return VideoClip(make_frame=make_frame, duration=duration)
