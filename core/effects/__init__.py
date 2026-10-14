"""Effects package - Cinematic visual effects."""
from .camera import apply_camera_movement
from .grading import grade_image_by_emotion, add_film_grain, add_vignette
from .captions import create_cinematic_caption
from .particles import create_particles_overlay
from .transitions import TransitionManager, crossfade_transition
from .overlays import OverlayManager, create_letterbox, create_lens_flare

__all__ = [
    "apply_camera_movement",
    "grade_image_by_emotion",
    "add_film_grain",
    "add_vignette",
    "create_cinematic_caption",
    "create_particles_overlay",
    "TransitionManager",
    "crossfade_transition",
    "OverlayManager",
    "create_letterbox",
    "create_lens_flare",
]
