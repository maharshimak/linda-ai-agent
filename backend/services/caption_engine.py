"""
Caption Engine - Advanced Word-by-Word Animated Captions
Creates professional-style captions synced with audio.
"""
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip
from dataclasses import dataclass
from typing import List, Tuple, Optional
import logging
import re

log = logging.getLogger(__name__)


@dataclass
class TimedWord:
    """A word with timing information."""
    text: str
    start: float
    end: float
    
    @property
    def duration(self) -> float:
        return self.end - self.start


# Caption style presets
CAPTION_STYLES = {
    "minimal": {
        "font": "Arial",
        "fontsize": 42,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "bg_color": None,
        "shadow": True,
    },
    "bold": {
        "font": "Arial-Bold",
        "fontsize": 52,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "bg_color": None,
        "shadow": True,
    },
    "gradient": {
        "font": "Arial-Bold",
        "fontsize": 48,
        "color": "white",
        "stroke_color": None,
        "stroke_width": 0,
        "bg_color": "rgba(139,92,246,0.85)",
        "shadow": False,
    },
    "neon": {
        "font": "Arial-Bold",
        "fontsize": 46,
        "color": "#00ff88",
        "stroke_color": "#003322",
        "stroke_width": 3,
        "bg_color": None,
        "shadow": True,
    },
    "modern": {
        "font": "Arial-Bold",
        "fontsize": 50,
        "color": "#FFFFFF",
        "stroke_color": "#a855f7",
        "stroke_width": 3,
        "bg_color": None,
        "shadow": True,
    },
}


class CaptionEngine:
    """
    Creates animated captions for videos.
    Supports word-by-word highlighting and multiple styles.
    """
    
    def __init__(self, style: str = "bold", video_size: Tuple[int, int] = (1080, 1920)):
        self.style_name = style
        self.style = CAPTION_STYLES.get(style, CAPTION_STYLES["bold"])
        self.video_size = video_size
        log.info(f"✍️ CaptionEngine initialized with '{style}' style")
    
    def estimate_word_timing(
        self, 
        text: str, 
        audio_duration: float,
        words_per_minute: float = 150
    ) -> List[TimedWord]:
        """
        Estimate word timing based on text length and audio duration.
        For precise sync, use Whisper transcription instead.
        """
        words = text.split()
        if not words:
            return []
        
        # Calculate time per word
        time_per_word = audio_duration / len(words)
        
        timed_words = []
        current_time = 0.0
        
        for word in words:
            # Adjust duration based on word length (longer words take more time)
            word_factor = 1.0 + (len(word) - 5) * 0.05
            word_duration = time_per_word * max(0.5, min(1.5, word_factor))
            
            timed_words.append(TimedWord(
                text=word,
                start=current_time,
                end=min(current_time + word_duration, audio_duration)
            ))
            current_time += word_duration
        
        return timed_words
    
    def create_caption_clip(
        self,
        text: str,
        start: float,
        duration: float,
        highlight: bool = False,
        position: Tuple = None
    ) -> TextClip:
        """Create a single caption text clip."""
        if position is None:
            position = ("center", self.video_size[1] * 0.82)
        
        # Style overrides for highlighted words
        style = self.style.copy()
        if highlight:
            style["color"] = "#a855f7"  # Purple highlight
            style["fontsize"] = int(style["fontsize"] * 1.15)
        
        try:
            clip = TextClip(
                text.upper(),
                font=style["font"],
                fontsize=style["fontsize"],
                color=style["color"],
                stroke_color=style.get("stroke_color"),
                stroke_width=style.get("stroke_width", 0),
                method="caption",
                size=(self.video_size[0] * 0.9, None),
                align="center"
            )
            
            clip = clip.set_position(position).set_start(start).set_duration(duration)
            return clip
            
        except Exception as e:
            log.warning(f"✍️ Caption creation failed: {e}, using fallback")
            # Fallback to simpler clip
            clip = TextClip(
                text.upper(),
                fontsize=48,
                color="white",
                method="label"
            )
            return clip.set_position(position).set_start(start).set_duration(duration)
    
    def create_sentence_captions(
        self,
        sentences: List[Tuple[str, float, float]],
        max_chars: int = 50
    ) -> List[TextClip]:
        """
        Create caption clips for full sentences.
        
        Args:
            sentences: List of (text, start_time, end_time) tuples
            max_chars: Maximum characters per line
            
        Returns:
            List of TextClip objects
        """
        clips = []
        
        for text, start, end in sentences:
            duration = end - start
            
            # Split long sentences
            if len(text) > max_chars:
                # Find good break point
                mid = len(text) // 2
                break_point = text.rfind(" ", 0, mid + 10)
                if break_point == -1:
                    break_point = mid
                
                line1 = text[:break_point].strip()
                line2 = text[break_point:].strip()
                text = f"{line1}\n{line2}"
            
            clip = self.create_caption_clip(text, start, duration)
            clips.append(clip)
        
        return clips
    
    def create_word_by_word_captions(
        self,
        timed_words: List[TimedWord],
        words_per_group: int = 3,
        highlight_current: bool = True
    ) -> List[TextClip]:
        """
        Create word-by-word animated captions.
        Shows groups of words and highlights the current one.
        
        Args:
            timed_words: List of TimedWord objects
            words_per_group: How many words to show at once
            highlight_current: Whether to highlight the current word
            
        Returns:
            List of TextClip objects
        """
        clips = []
        
        for i in range(0, len(timed_words), words_per_group):
            group = timed_words[i:i + words_per_group]
            
            if not group:
                continue
            
            # Combine words in group
            group_text = " ".join(w.text for w in group)
            start_time = group[0].start
            end_time = group[-1].end
            duration = end_time - start_time
            
            clip = self.create_caption_clip(
                group_text,
                start_time,
                duration,
                highlight=False
            )
            clips.append(clip)
        
        log.info(f"✍️ Created {len(clips)} caption clips")
        return clips
    
    def add_captions_to_video(
        self,
        video_clip,
        narration_text: str,
        audio_duration: float
    ):
        """
        Add captions to a video clip.
        
        Args:
            video_clip: The video clip to add captions to
            narration_text: The narration text
            audio_duration: Duration of the audio
            
        Returns:
            Video clip with captions composited
        """
        # Estimate word timing
        timed_words = self.estimate_word_timing(narration_text, audio_duration)
        
        # Create caption clips
        caption_clips = self.create_word_by_word_captions(timed_words)
        
        if not caption_clips:
            return video_clip
        
        # Composite
        return CompositeVideoClip([video_clip] + caption_clips)


def get_available_styles() -> List[str]:
    """Return list of available caption styles."""
    return list(CAPTION_STYLES.keys())


def create_caption_engine(style: str = "bold", video_size: Tuple[int, int] = (1080, 1920)) -> CaptionEngine:
    """Factory function to create a caption engine."""
    return CaptionEngine(style, video_size)
