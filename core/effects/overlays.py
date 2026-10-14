"""
Premium Overlays
Cinematic overlay effects for professional video production.
"""
import math
import random
import numpy as np
from typing import Tuple, Dict, Optional
from PIL import Image, ImageDraw, ImageFilter

from ..utils.helpers import lerp


def create_letterbox(
    canvas_size: Tuple[int, int] = (1080, 1920),
    aspect_ratio: float = 2.35,
    bar_color: Tuple[int, int, int] = (0, 0, 0),
    opacity: float = 1.0
) -> Image.Image:
    """
    Create cinematic letterbox bars.
    
    Args:
        canvas_size: (width, height) of the output
        aspect_ratio: Target aspect ratio (2.35 for cinemascope, 2.39 for full scope)
        bar_color: RGB color of bars
        opacity: Bar opacity (0.0 to 1.0)
        
    Returns:
        RGBA image with letterbox bars
    """
    w, h = canvas_size
    
    # Calculate visible height for target aspect ratio
    # For 9:16 (0.5625 ratio) to show 2.35:1 content
    visible_width = w
    visible_height = int(visible_width / aspect_ratio)
    
    # Bar height
    bar_height = (h - visible_height) // 2
    
    # Create overlay
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    alpha = int(255 * opacity)
    bar_rgba = (*bar_color, alpha)
    
    # Top bar
    draw.rectangle([(0, 0), (w, bar_height)], fill=bar_rgba)
    
    # Bottom bar
    draw.rectangle([(0, h - bar_height), (w, h)], fill=bar_rgba)
    
    return overlay


def create_lens_flare(
    canvas_size: Tuple[int, int] = (1080, 1920),
    position: Tuple[float, float] = (0.7, 0.3),
    intensity: float = 0.5,
    color: Tuple[int, int, int] = (255, 200, 100)
) -> Image.Image:
    """
    Create an anamorphic lens flare overlay.
    
    Args:
        canvas_size: (width, height) of the output
        position: Normalized position of flare source (0-1, 0-1)
        intensity: Flare intensity (0.0 to 1.0)
        color: Base flare color
        
    Returns:
        RGBA image with lens flare
    """
    w, h = canvas_size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Source position
    src_x = int(position[0] * w)
    src_y = int(position[1] * h)
    
    # Main flare (horizontal anamorphic streak)
    streak_length = int(w * 0.8 * intensity)
    streak_height = int(6 * intensity)
    
    for i in range(streak_length):
        # Fade from center
        dist_from_src = abs(src_x - (src_x - streak_length // 2 + i))
        alpha = int(255 * intensity * (1 - dist_from_src / (streak_length / 2)))
        alpha = max(0, min(255, alpha))
        
        x = src_x - streak_length // 2 + i
        if 0 <= x < w:
            draw.line(
                [(x, src_y - streak_height), (x, src_y + streak_height)],
                fill=(*color, alpha),
                width=1
            )
    
    # Secondary flares (chromatic aberration)
    num_flares = 5
    for i in range(num_flares):
        # Position along line from source to opposite corner
        t = (i + 1) / (num_flares + 1)
        flare_x = int(lerp(src_x, w - src_x, t))
        flare_y = int(lerp(src_y, h - src_y, t))
        
        # Flare size decreases with distance
        size = int(30 * (1 - t * 0.5) * intensity)
        alpha = int(100 * intensity * (1 - t * 0.3))
        
        # Chromatic colors
        colors = [
            (255, 100, 50, alpha),   # Orange
            (50, 150, 255, alpha),   # Blue
            (255, 50, 100, alpha),   # Pink
        ]
        flare_color = colors[i % len(colors)]
        
        draw.ellipse(
            [(flare_x - size, flare_y - size), (flare_x + size, flare_y + size)],
            fill=flare_color
        )
    
    # Apply blur for realistic glow
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=3))
    
    return overlay


def create_light_leak(
    canvas_size: Tuple[int, int] = (1080, 1920),
    position: str = "top_right",
    intensity: float = 0.3,
    color: Tuple[int, int, int] = (255, 180, 100)
) -> Image.Image:
    """
    Create a vintage light leak overlay.
    
    Args:
        canvas_size: (width, height) of the output
        position: 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'random'
        intensity: Leak intensity (0.0 to 1.0)
        color: Base leak color
        
    Returns:
        RGBA image with light leak
    """
    w, h = canvas_size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # Position mapping
    positions = {
        "top_left": (0, 0),
        "top_right": (w, 0),
        "bottom_left": (0, h),
        "bottom_right": (w, h),
    }
    
    if position == "random":
        position = random.choice(list(positions.keys()))
    
    center_x, center_y = positions.get(position, positions["top_right"])
    
    # Create radial gradient
    arr = np.zeros((h, w, 4), dtype=np.float32)
    
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
    max_dist = np.sqrt(w**2 + h**2) * 0.6
    
    # Gradient falloff
    gradient = 1 - np.clip(distances / max_dist, 0, 1)
    gradient = gradient ** 2  # More concentrated near corner
    
    # Apply color and intensity
    alpha = (gradient * 255 * intensity).astype(np.uint8)
    arr[:, :, 0] = color[0] * gradient
    arr[:, :, 1] = color[1] * gradient
    arr[:, :, 2] = color[2] * gradient
    arr[:, :, 3] = alpha
    
    overlay = Image.fromarray(arr.astype(np.uint8), mode="RGBA")
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=50))
    
    return overlay


def create_animated_grain(
    canvas_size: Tuple[int, int] = (1080, 1920),
    intensity: float = 0.03,
    time: float = 0.0
) -> Image.Image:
    """
    Create animated film grain overlay.
    
    Args:
        canvas_size: (width, height) of the output
        intensity: Grain intensity (0.0 to 0.1 recommended)
        time: Time in seconds (for animation seed)
        
    Returns:
        RGBA image with film grain
    """
    w, h = canvas_size
    
    # Use time as seed for reproducible but animated grain
    seed = int(time * 24) % 10000  # 24 different patterns per second
    np.random.seed(seed)
    
    # Generate noise
    noise = np.random.normal(0.5, intensity, (h, w))
    noise = np.clip(noise, 0, 1).astype(np.float32)
    
    # Convert to RGBA
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    gray = (noise * 255).astype(np.uint8)
    arr[:, :, 0] = gray
    arr[:, :, 1] = gray
    arr[:, :, 2] = gray
    arr[:, :, 3] = (noise * 255 * 0.3).astype(np.uint8)  # Low opacity
    
    return Image.fromarray(arr, mode="RGBA")


def create_bokeh_overlay(
    canvas_size: Tuple[int, int] = (1080, 1920),
    num_particles: int = 30,
    intensity: float = 0.4,
    palette: Optional[Dict[str, Tuple[int, int, int]]] = None
) -> Image.Image:
    """
    Create floating bokeh light particles overlay.
    
    Args:
        canvas_size: (width, height) of the output
        num_particles: Number of bokeh particles
        intensity: Overall intensity (0.0 to 1.0)
        palette: Color palette with 'accent' and 'primary' keys
        
    Returns:
        RGBA image with bokeh particles
    """
    w, h = canvas_size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Default colors
    if palette:
        colors = [
            palette.get("accent", (255, 215, 0)),
            palette.get("primary", (255, 147, 41)),
        ]
    else:
        colors = [
            (255, 215, 0),    # Gold
            (255, 147, 41),   # Orange
            (255, 255, 255),  # White
        ]
    
    for i in range(num_particles):
        # Random position
        x = random.randint(0, w)
        y = random.randint(0, h)
        
        # Random size (larger = more alpha)
        size = random.randint(5, 40)
        
        # Random color from palette
        color = random.choice(colors)
        
        # Alpha based on size and intensity
        alpha = int(min(255, 80 * intensity * (size / 30)))
        
        # Draw soft circle
        draw.ellipse(
            [(x - size, y - size), (x + size, y + size)],
            fill=(*color, alpha)
        )
    
    # Apply heavy blur for soft bokeh look
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=15))
    
    return overlay


class OverlayManager:
    """
    Manages cinematic overlays for video production.
    """
    
    def __init__(self, canvas_size: Tuple[int, int] = (1080, 1920)):
        """
        Initialize overlay manager.
        
        Args:
            canvas_size: Default canvas size for overlays
        """
        self.canvas_size = canvas_size
        self.letterbox = None
        self.lens_flare = None
        self.light_leak = None
    
    def get_letterbox(
        self, 
        aspect_ratio: float = 2.35,
        opacity: float = 1.0
    ) -> Image.Image:
        """Get or create letterbox overlay."""
        return create_letterbox(self.canvas_size, aspect_ratio, opacity=opacity)
    
    def get_lens_flare(
        self,
        position: Tuple[float, float] = (0.8, 0.2),
        intensity: float = 0.5
    ) -> Image.Image:
        """Get lens flare overlay."""
        return create_lens_flare(self.canvas_size, position, intensity)
    
    def get_light_leak(
        self,
        position: str = "random",
        intensity: float = 0.25
    ) -> Image.Image:
        """Get light leak overlay."""
        return create_light_leak(self.canvas_size, position, intensity)
    
    def get_grain(self, time: float = 0.0, intensity: float = 0.03) -> Image.Image:
        """Get animated grain overlay for a specific time."""
        return create_animated_grain(self.canvas_size, intensity, time)
    
    def get_bokeh(
        self,
        num_particles: int = 30,
        intensity: float = 0.4,
        palette: Optional[Dict] = None
    ) -> Image.Image:
        """Get bokeh particles overlay."""
        return create_bokeh_overlay(self.canvas_size, num_particles, intensity, palette)
    
    def composite_overlay(
        self,
        base_frame: np.ndarray,
        overlay: Image.Image,
        blend_mode: str = "screen"
    ) -> np.ndarray:
        """
        Composite an overlay onto a frame.
        
        Args:
            base_frame: Base frame as numpy array (HxWx3 uint8)
            overlay: RGBA overlay image
            blend_mode: 'screen', 'add', 'overlay', 'normal'
            
        Returns:
            Composited frame as numpy array
        """
        base = Image.fromarray(base_frame).convert("RGBA")
        
        if blend_mode == "normal":
            # Simple alpha composite
            base.paste(overlay, (0, 0), overlay)
        elif blend_mode == "screen":
            # Screen blend mode
            base_arr = np.array(base).astype(np.float32) / 255
            over_arr = np.array(overlay).astype(np.float32) / 255
            alpha = over_arr[:, :, 3:4]
            over_rgb = over_arr[:, :, :3]
            base_rgb = base_arr[:, :, :3]
            
            # Screen: 1 - (1-a)(1-b)
            screened = 1 - (1 - base_rgb) * (1 - over_rgb)
            result = base_rgb * (1 - alpha) + screened * alpha
            result = (result * 255).astype(np.uint8)
            return result
        elif blend_mode == "add":
            # Additive blend
            base_arr = np.array(base)[:, :, :3].astype(np.float32)
            over_arr = np.array(overlay).astype(np.float32)
            alpha = over_arr[:, :, 3:4] / 255
            over_rgb = over_arr[:, :, :3]
            
            result = base_arr + over_rgb * alpha
            result = np.clip(result, 0, 255).astype(np.uint8)
            return result
        
        return np.array(base.convert("RGB"))
