"""
Compatibility Utilities
Handles Pillow/MoviePy version differences and other library quirks.
"""
import sys
import numpy as np
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


# ═══════════════════════════════════════════════════════════════
# PILLOW COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

# MoviePy and older code may reference ANTIALIAS
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS


def text_size(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, text: str) -> Tuple[int, int]:
    """
    Cross-version safe text size measurement.
    Prefers draw.textbbox, falls back to font.getbbox, then rough estimate.
    """
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            # Rough fallback
            return (len(text) * 12, 24)


def multiline_text_bbox(
    draw: ImageDraw.ImageDraw, 
    text: str, 
    font: ImageFont.ImageFont, 
    spacing: int = 8
) -> Tuple[int, int, int, int]:
    """
    Return bbox for multiline text, compatible with new Pillow.
    """
    try:
        return draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    except Exception:
        # Fallback: approximate via per-line width/height
        lines = text.splitlines() or [text]
        widths = []
        heights = []
        for line in lines:
            w, h = text_size(draw, font, line)
            widths.append(w)
            heights.append(h)
        w = max(widths) if widths else 0
        h = sum(heights) + spacing * (len(lines) - 1)
        return (0, 0, w, h)


# ═══════════════════════════════════════════════════════════════
# MOVIEPY COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

def to_rgb_uint8(arr: np.ndarray) -> np.ndarray:
    """
    Ensure MoviePy-safe frame: HxWx3, uint8 RGB.
    Handles grayscale, RGBA, and dtype conversion.
    """
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    if arr.ndim == 2:  # grayscale → RGB
        arr = np.stack([arr] * 3, axis=-1)
    if arr.shape[-1] == 4:  # RGBA → RGB
        arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


# ═══════════════════════════════════════════════════════════════
# CONSOLE COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

def setup_console_encoding():
    """
    Ensure console handles UTF-8 to avoid cp1252 emoji crashes on Windows.
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Run on import
setup_console_encoding()
