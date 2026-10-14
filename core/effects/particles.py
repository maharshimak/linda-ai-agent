"""
Particle Effects
Ambient particle overlays for cinematic atmosphere.
"""
import numpy as np
from typing import Dict, Tuple, Callable
from PIL import Image, ImageDraw

from ..utils.compatibility import to_rgb_uint8


def create_particles_overlay(
    duration: float,
    size: Tuple[int, int] = (1080, 1920),
    palette: Dict[str, Tuple[int, int, int]] = None,
    particle_count: int = 40,
    speed: float = 30.0
) -> Callable[[float], np.ndarray]:
    """
    Create a function that generates particle overlay frames.
    
    Args:
        duration: Total duration in seconds
        size: (width, height) of the overlay
        palette: Color palette with 'accent' key
        particle_count: Number of particles
        speed: Vertical movement speed in pixels per second
        
    Returns:
        Function that takes time t and returns numpy frame
    """
    w, h = size
    accent = (palette or {}).get("accent", (255, 215, 0))
    
    # Pre-generate particle positions and sizes
    np.random.seed(42)  # Reproducible particles
    particles = []
    for i in range(particle_count):
        particles.append({
            "x": np.random.randint(0, w),
            "y_base": np.random.randint(0, h),
            "size": 2 + (i % 3),
            "speed_mult": 1 + (i % 3) * 0.5
        })
    
    def make_frame(t: float) -> np.ndarray:
        """Generate particle frame at time t."""
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        for p in particles:
            # Calculate vertical position with looping
            y = (p["y_base"] - int(t * speed * p["speed_mult"])) % h
            x = p["x"]
            s = p["size"]
            
            # Draw particle with slight transparency effect via smaller size
            draw.ellipse(
                [x, y, x + s, y + s],
                fill=accent
            )
        
        return to_rgb_uint8(np.array(canvas))
    
    return make_frame


def create_dust_overlay(
    size: Tuple[int, int] = (1080, 1920),
    density: float = 0.001
) -> Callable[[float], np.ndarray]:
    """
    Create a dust/grain overlay with subtle floating particles.
    
    Args:
        size: (width, height)
        density: Particle density (0.0-0.01)
        
    Returns:
        Function that takes time t and returns numpy frame
    """
    w, h = size
    
    def make_frame(t: float) -> np.ndarray:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Random dust particles
        num_particles = int(w * h * density)
        xs = np.random.randint(0, w, num_particles)
        ys = np.random.randint(0, h, num_particles)
        
        # Vary brightness
        brightness = np.random.randint(100, 255, num_particles)
        
        for x, y, b in zip(xs, ys, brightness):
            # Small 1-2 pixel particles
            size = np.random.choice([1, 2])
            x2, y2 = min(x + size, w), min(y + size, h)
            canvas[y:y2, x:x2] = b
        
        return canvas
    
    return make_frame


def create_light_leak(
    size: Tuple[int, int] = (1080, 1920),
    color: Tuple[int, int, int] = (255, 147, 41)
) -> Callable[[float], np.ndarray]:
    """
    Create an animated light leak effect.
    
    Args:
        size: (width, height)
        color: Base color of the light leak
        
    Returns:
        Function that takes time t and returns numpy frame
    """
    w, h = size
    
    def make_frame(t: float) -> np.ndarray:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Animated gradient from corner
        phase = (t * 0.5) % 1.0  # Slow cycle
        
        # Create radial gradient from top-right
        y_grid, x_grid = np.ogrid[:h, :w]
        center_x = w + int(w * 0.3 * np.sin(phase * np.pi * 2))
        center_y = -int(h * 0.2 * np.cos(phase * np.pi * 2))
        
        dist = np.sqrt((x_grid - center_x)**2 + (y_grid - center_y)**2)
        max_dist = np.sqrt(w**2 + h**2) * 0.6
        
        # Create falloff
        intensity = np.clip(1 - (dist / max_dist), 0, 1)
        intensity = intensity ** 2  # Quadratic falloff
        
        # Apply color with varying intensity
        base_alpha = 0.2 + 0.1 * np.sin(phase * np.pi * 4)
        
        for c in range(3):
            canvas[:, :, c] = (intensity * color[c] * base_alpha).astype(np.uint8)
        
        return canvas
    
    return make_frame


def create_bokeh_overlay(
    size: Tuple[int, int] = (1080, 1920),
    bokeh_count: int = 15,
    max_radius: int = 80
) -> Callable[[float], np.ndarray]:
    """
    Create animated bokeh circles overlay.
    
    Args:
        size: (width, height)
        bokeh_count: Number of bokeh circles
        max_radius: Maximum radius of bokeh circles
        
    Returns:
        Function that takes time t and returns numpy frame
    """
    w, h = size
    
    # Pre-generate bokeh positions
    np.random.seed(123)
    bokehs = []
    for i in range(bokeh_count):
        bokehs.append({
            "x": np.random.randint(0, w),
            "y": np.random.randint(0, h),
            "radius": np.random.randint(20, max_radius),
            "alpha": np.random.uniform(0.1, 0.3),
            "color": (
                np.random.randint(200, 255),
                np.random.randint(200, 255),
                np.random.randint(200, 255)
            ),
            "phase": np.random.uniform(0, np.pi * 2)
        })
    
    def make_frame(t: float) -> np.ndarray:
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        for b in bokehs:
            # Animate alpha
            alpha = b["alpha"] * (0.8 + 0.2 * np.sin(t * 2 + b["phase"]))
            color = (*b["color"], int(alpha * 255))
            
            # Subtle position drift
            x = b["x"] + int(10 * np.sin(t * 0.5 + b["phase"]))
            y = b["y"] + int(5 * np.cos(t * 0.3 + b["phase"]))
            r = b["radius"]
            
            # Draw soft circle (using alpha for softness)
            draw.ellipse(
                [x - r, y - r, x + r, y + r],
                fill=color,
                outline=None
            )
        
        # Convert to RGB (blend with black)
        rgb = Image.new("RGB", (w, h), (0, 0, 0))
        rgb.paste(canvas, (0, 0), canvas)
        
        return to_rgb_uint8(np.array(rgb))
    
    return make_frame
