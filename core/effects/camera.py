"""
Camera Effects
Camera movement animations for video clips.
"""
import math
from typing import Tuple
from PIL import Image

from ..models import CameraMove
from ..utils.helpers import lerp, ease_out_cubic


def get_movement_params(camera_move: CameraMove) -> Tuple[float, float, Tuple[int, int]]:
    """
    Get scale and offset parameters for a camera movement.
    Returns: (start_scale, end_scale, (max_offset_x, max_offset_y))
    """
    params = {
        CameraMove.DOLLY_IN: (1.15, 1.05, (0, 0)),
        CameraMove.DOLLY_OUT: (1.05, 1.15, (0, 0)),
        CameraMove.PAN_RIGHT: (1.10, 1.10, (-80, 0)),
        CameraMove.PAN_LEFT: (1.10, 1.10, (80, 0)),
        CameraMove.CRANE_UP: (1.08, 1.08, (0, 60)),
        CameraMove.CRANE_DOWN: (1.08, 1.08, (0, -60)),
        CameraMove.ORBIT: (1.10, 1.10, (50, 30)),
        CameraMove.PARALLAX: (1.08, 1.12, (40, 0)),
        CameraMove.DUTCH_ANGLE: (1.10, 1.10, (30, 0)),
        CameraMove.STATIC: (1.02, 1.02, (0, 0)),
    }
    return params.get(camera_move, params[CameraMove.DOLLY_IN])


def apply_camera_movement(
    img: Image.Image,
    camera_move: CameraMove,
    t: float,
    duration: float
) -> Tuple[float, Tuple[int, int]]:
    """
    Calculate scale and offset for a camera movement at time t.
    
    Args:
        img: The source image (for reference, not modified)
        camera_move: The type of camera movement
        t: Current time in the animation
        duration: Total duration of the animation
        
    Returns:
        (scale_factor, (offset_x, offset_y))
    """
    if duration <= 0:
        duration = 0.001
    
    progress = min(max(t / duration, 0), 1)
    eased = ease_out_cubic(progress)
    
    start_scale, end_scale, max_offset = get_movement_params(camera_move)
    
    # Interpolate scale
    scale = lerp(start_scale, end_scale, eased)
    
    # Calculate offset based on movement type
    if camera_move == CameraMove.ORBIT:
        offset_x = int(max_offset[0] * math.sin(eased * math.pi))
        offset_y = int(max_offset[1] * math.cos(eased * math.pi))
    elif camera_move == CameraMove.PARALLAX:
        offset_x = int(max_offset[0] * math.sin(eased * 2 * math.pi))
        offset_y = 0
    elif camera_move in [CameraMove.PAN_LEFT, CameraMove.PAN_RIGHT]:
        offset_x = int(max_offset[0] * eased)
        offset_y = 0
    elif camera_move in [CameraMove.CRANE_UP, CameraMove.CRANE_DOWN]:
        offset_x = 0
        offset_y = int(max_offset[1] * eased)
    elif camera_move == CameraMove.DUTCH_ANGLE:
        offset_x = int(max_offset[0] * math.sin(eased * 2 * math.pi))
        offset_y = 0
    else:
        # Zoom movements (DOLLY_IN, DOLLY_OUT, STATIC)
        offset_x = 0
        offset_y = 0
    
    return scale, (offset_x, offset_y)


def apply_camera_to_frame(
    img: Image.Image,
    camera_move: CameraMove,
    t: float,
    duration: float,
    canvas_size: Tuple[int, int]
) -> Image.Image:
    """
    Apply camera movement and return a new frame.
    
    Args:
        img: Source image
        camera_move: Type of movement
        t: Current time
        duration: Total duration
        canvas_size: (width, height) of output canvas
        
    Returns:
        New PIL Image with camera movement applied
    """
    scale, offset = apply_camera_movement(img, camera_move, t, duration)
    
    canvas_w, canvas_h = canvas_size
    new_w = int(canvas_w * scale)
    new_h = int(canvas_h * scale)
    
    # Resize image
    scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Calculate paste position (centered with offset)
    x = (canvas_w - new_w) // 2 + offset[0]
    y = (canvas_h - new_h) // 2 + offset[1]
    
    # Create canvas and paste
    canvas = Image.new("RGB", canvas_size, (0, 0, 0))
    canvas.paste(scaled, (x, y))
    
    return canvas
