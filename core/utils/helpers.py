"""
Common Helper Utilities
"""
import os
import re
import math
from pathlib import Path
from typing import Optional


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    Convert a string to a safe filename.
    Removes special characters, limits length.
    """
    # Replace non-alphanumeric with underscores
    safe = re.sub(r'[^\w\s-]', '_', name)
    # Replace whitespace with underscores
    safe = re.sub(r'\s+', '_', safe)
    # Remove consecutive underscores
    safe = re.sub(r'_+', '_', safe)
    # Trim and limit length
    return safe.strip('_')[:max_length]


def format_srt_timestamp(seconds: float) -> str:
    """
    Format seconds as SRT timestamp: HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def estimate_duration(text: str, words_per_minute: float = 150) -> float:
    """
    Estimate speaking duration for text.
    Default 150 WPM is natural conversational pace.
    """
    word_count = len(text.split())
    return (word_count / words_per_minute) * 60


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out."""
    return 1 - pow(1 - t, 3)


def ease_out_expo(t: float) -> float:
    """Exponential ease-out."""
    return 1 if t == 1 else 1 - pow(2, -10 * t)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def find_ffmpeg() -> Optional[str]:
    """
    Find FFmpeg executable.
    Returns path or None if not found.
    """
    import shutil
    
    # Check environment variable first
    env_path = os.getenv("FFMPEG_BINARY")
    if env_path and Path(env_path).exists():
        return env_path
    
    # Check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    # Try imageio-ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    
    # Common Windows locations
    common_paths = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path.cwd() / "Tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]
    
    for p in common_paths:
        if p.exists():
            return str(p)
    
    return None
