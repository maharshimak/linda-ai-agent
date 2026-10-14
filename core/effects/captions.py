"""
Cinematic Captions
Stylized text overlays for video scenes.
"""
import textwrap
import numpy as np
from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ..utils.compatibility import text_size, multiline_text_bbox


# Default fonts
WINDOWS_FONT = r"C:\Windows\Fonts\arial.ttf"
WINDOWS_FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def load_font(path: str, size: int) -> ImageFont.ImageFont:
    """Load a font with fallbacks."""
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype(WINDOWS_FONT, size)
        except Exception:
            return ImageFont.load_default()


def create_cinematic_caption(
    text: str,
    palette: Dict[str, Tuple[int, int, int]],
    font_path: str = WINDOWS_FONT_BOLD,
    style: str = "modern",
    max_width: int = 24
) -> Image.Image:
    """
    Create a stylized caption image with transparent background.
    
    Args:
        text: The caption text
        palette: Color palette dict with 'accent', 'text', 'shadow' keys
        font_path: Path to the font file
        style: Caption style ('modern', 'classic', 'bold')
        max_width: Maximum characters per line
        
    Returns:
        RGBA PIL Image with the caption
    """
    # Determine font size based on text length
    if len(text) < 30:
        base_size = 72
    elif len(text) < 50:
        base_size = 64
    else:
        base_size = 56
    
    font = load_font(font_path, base_size)
    font_bold = load_font(WINDOWS_FONT_BOLD, base_size)
    
    # Wrap text
    wrapped = textwrap.fill(text, width=max_width)
    
    # Calculate dimensions
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = multiline_text_bbox(draw, wrapped, font=font, spacing=8)
    
    # Add padding
    w = bbox[2] - bbox[0] + 80
    h = bbox[3] - bbox[1] + 60
    
    # Create canvas
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if style == "modern":
        # Rounded rectangle background
        bar_height = h - 20
        bar = Image.new("RGBA", (w - 20, bar_height), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar)
        bar_draw.rounded_rectangle(
            [(0, 0), (w - 20, bar_height)],
            radius=12,
            fill=(0, 0, 0, 180)
        )
        bar = bar.filter(ImageFilter.GaussianBlur(2))
        img.paste(bar, (10, 10), bar)
        
        # Accent bar
        accent_color = palette.get("accent", (255, 215, 0))
        draw.rounded_rectangle(
            [(15, 15), (25, h - 15)],
            radius=3,
            fill=accent_color
        )
        
        # Shadow text
        shadow_color = (*palette.get("shadow", (0, 0, 0)), 200)
        for offset in [(0, 2), (2, 0), (-2, 0), (0, -2)]:
            draw.multiline_text(
                (w // 2 + offset[0], h // 2 + offset[1]),
                wrapped,
                font=font_bold,
                fill=shadow_color,
                spacing=8,
                align="center",
                anchor="mm"
            )
        
        # Main text
        text_color = palette.get("text", (255, 255, 255))
        draw.multiline_text(
            (w // 2, h // 2),
            wrapped,
            font=font_bold,
            fill=text_color,
            spacing=8,
            align="center",
            anchor="mm"
        )
        
    elif style == "classic":
        # Text with stroke only (no background)
        text_color = palette.get("text", (255, 255, 255))
        stroke_color = (0, 0, 0, 255)
        
        draw.multiline_text(
            (w // 2, h // 2),
            wrapped,
            font=font_bold,
            fill=text_color,
            spacing=8,
            align="center",
            anchor="mm",
            stroke_width=4,
            stroke_fill=stroke_color
        )
        
    elif style == "bold":
        # Large bold text with heavy shadow
        shadow_color = (*palette.get("shadow", (0, 0, 0)), 255)
        
        # Multiple shadow layers
        for i in range(6, 0, -1):
            alpha = int(255 * (1 - i / 8))
            draw.multiline_text(
                (w // 2 + i, h // 2 + i),
                wrapped,
                font=font_bold,
                fill=(*shadow_color[:3], alpha),
                spacing=8,
                align="center",
                anchor="mm"
            )
        
        # Main text
        text_color = palette.get("text", (255, 255, 255))
        draw.multiline_text(
            (w // 2, h // 2),
            wrapped,
            font=font_bold,
            fill=text_color,
            spacing=8,
            align="center",
            anchor="mm"
        )
    
    else:
        # Fallback: simple text
        text_color = palette.get("text", (255, 255, 255))
        draw.multiline_text(
            (w // 2, h // 2),
            wrapped,
            font=font,
            fill=text_color,
            spacing=8,
            align="center",
            anchor="mm",
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255)
        )
    
    return img


def create_title_card(
    title: str,
    palette: Dict[str, Tuple[int, int, int]],
    canvas_size: Tuple[int, int] = (1080, 1920),
    font_path: str = WINDOWS_FONT_BOLD
) -> Image.Image:
    """
    Create a full-screen title card.
    
    Args:
        title: The title text
        palette: Color palette
        canvas_size: (width, height) of the canvas
        font_path: Path to font file
        
    Returns:
        RGB PIL Image with title card
    """
    w, h = canvas_size
    
    # Create dark background
    img = Image.new("RGB", (w, h), (5, 5, 15))
    draw = ImageDraw.Draw(img)
    
    # Load font
    font_size = 96
    font = load_font(font_path, font_size)
    
    # Wrap title
    wrapped = textwrap.fill(title, width=18)
    
    # Calculate text bounds
    bbox = multiline_text_bbox(draw, wrapped, font=font, spacing=12)
    
    # Draw glow effect
    accent = palette.get("accent", (255, 215, 0))
    for offset in [(0, 3), (3, 0), (-3, 0), (0, -3), (2, 2), (-2, 2)]:
        draw.multiline_text(
            (w // 2 + offset[0], h // 2 + offset[1]),
            wrapped,
            font=font,
            fill=(accent[0], accent[1], accent[2], 100) if len(accent) == 3 else accent,
            spacing=12,
            align="center",
            anchor="mm"
        )
    
    # Draw main text
    text_color = palette.get("text", (255, 255, 255))
    draw.multiline_text(
        (w // 2, h // 2),
        wrapped,
        font=font,
        fill=text_color,
        spacing=12,
        align="center",
        anchor="mm"
    )
    
    # Add underline accent
    line_y = h // 2 + bbox[3] // 2 + 20
    draw.rectangle(
        [(w // 2 - 80, line_y), (w // 2 + 80, line_y + 4)],
        fill=accent
    )
    
    return img
