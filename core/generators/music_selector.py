"""
Music Selector
Intelligent background music selection based on theme and emotion.
"""
import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

log = logging.getLogger("core.generators.music_selector")


class MusicMood(Enum):
    """Music mood categories."""
    EPIC = "epic"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"
    CALM = "calm"
    INTENSE = "intense"
    SUSPENSE = "suspense"
    MELANCHOLY = "melancholy"
    NEUTRAL = "neutral"


# Theme to mood mapping
THEME_TO_MOOD: Dict[str, MusicMood] = {
    "epic": MusicMood.EPIC,
    "mysterious": MusicMood.MYSTERIOUS,
    "inspiring": MusicMood.UPLIFTING,
    "uplifting": MusicMood.UPLIFTING,
    "intense": MusicMood.INTENSE,
    "peaceful": MusicMood.CALM,
    "calm": MusicMood.CALM,
    "suspense": MusicMood.SUSPENSE,
    "suspenseful": MusicMood.SUSPENSE,
    "melancholy": MusicMood.MELANCHOLY,
    "sad": MusicMood.MELANCHOLY,
    "neutral": MusicMood.NEUTRAL,
    "corporate": MusicMood.NEUTRAL,
}


class MusicSelector:
    """
    Selects appropriate background music based on video theme and emotion.
    
    Supports multiple BGM tracks organized by mood in the assets/bgm directory.
    Falls back to any available track if mood-specific tracks aren't found.
    """
    
    def __init__(self, bgm_dir: Optional[Path] = None):
        """
        Initialize music selector.
        
        Args:
            bgm_dir: Path to background music directory.
                     Expected structure: bgm_dir/{mood}/*.mp3 or bgm_dir/*.mp3
        """
        self.bgm_dir = bgm_dir or Path("assets/bgm")
        self._scan_library()
    
    def _scan_library(self):
        """Scan the BGM directory and catalog available tracks."""
        self.library: Dict[MusicMood, List[Path]] = {mood: [] for mood in MusicMood}
        self.all_tracks: List[Path] = []
        
        if not self.bgm_dir.exists():
            log.warning(f"BGM directory not found: {self.bgm_dir}")
            return
        
        # Check for mood-specific subdirectories
        for mood in MusicMood:
            mood_dir = self.bgm_dir / mood.value
            if mood_dir.exists():
                tracks = list(mood_dir.glob("*.mp3")) + list(mood_dir.glob("*.wav"))
                self.library[mood].extend(tracks)
                self.all_tracks.extend(tracks)
        
        # Also scan root directory for any tracks
        root_tracks = list(self.bgm_dir.glob("*.mp3")) + list(self.bgm_dir.glob("*.wav"))
        self.all_tracks.extend(root_tracks)
        
        # Categorize root tracks by filename keywords
        for track in root_tracks:
            name_lower = track.stem.lower()
            categorized = False
            
            for keyword, mood in [
                ("epic", MusicMood.EPIC),
                ("cinematic", MusicMood.EPIC),
                ("heroic", MusicMood.EPIC),
                ("mysterious", MusicMood.MYSTERIOUS),
                ("dark", MusicMood.MYSTERIOUS),
                ("ambient", MusicMood.MYSTERIOUS),
                ("uplifting", MusicMood.UPLIFTING),
                ("inspiring", MusicMood.UPLIFTING),
                ("happy", MusicMood.UPLIFTING),
                ("calm", MusicMood.CALM),
                ("peaceful", MusicMood.CALM),
                ("relaxing", MusicMood.CALM),
                ("intense", MusicMood.INTENSE),
                ("action", MusicMood.INTENSE),
                ("suspense", MusicMood.SUSPENSE),
                ("tension", MusicMood.SUSPENSE),
                ("sad", MusicMood.MELANCHOLY),
                ("emotional", MusicMood.MELANCHOLY),
            ]:
                if keyword in name_lower:
                    self.library[mood].append(track)
                    categorized = True
                    break
            
            if not categorized:
                # Add uncategorized tracks to EPIC as default
                self.library[MusicMood.EPIC].append(track)
        
        log.info(f"🎵 Music library loaded: {len(self.all_tracks)} tracks")
        for mood, tracks in self.library.items():
            if tracks:
                log.debug(f"   {mood.value}: {len(tracks)} tracks")
    
    def select(
        self,
        theme: Optional[str] = None,
        mood: Optional[MusicMood] = None
    ) -> Optional[Path]:
        """
        Select a background music track.
        
        Args:
            theme: Video theme string (e.g., "epic", "mysterious")
            mood: Explicit MusicMood enum value
            
        Returns:
            Path to selected BGM file, or None if no tracks available
        """
        # Determine target mood
        if mood is None and theme:
            mood = THEME_TO_MOOD.get(theme.lower(), MusicMood.EPIC)
        elif mood is None:
            mood = MusicMood.EPIC
        
        # Try mood-specific tracks first
        if self.library[mood]:
            track = random.choice(self.library[mood])
            log.info(f"🎵 Selected BGM for {mood.value}: {track.name}")
            return track
        
        # Fall back to any available track
        if self.all_tracks:
            track = random.choice(self.all_tracks)
            log.info(f"🎵 Selected fallback BGM: {track.name}")
            return track
        
        log.warning("No background music available")
        return None
    
    def get_mood_from_emotions(self, emotions: List[str]) -> MusicMood:
        """
        Analyze a list of emotion tags and determine overall mood.
        
        Args:
            emotions: List of emotion strings (e.g., ["epic", "intense", "uplifting"])
            
        Returns:
            Dominant MusicMood for the video
        """
        if not emotions:
            return MusicMood.EPIC
        
        # Count occurrences of each mood
        mood_counts: Dict[MusicMood, int] = {mood: 0 for mood in MusicMood}
        
        for emotion in emotions:
            emotion_lower = emotion.lower()
            if emotion_lower in THEME_TO_MOOD:
                mood_counts[THEME_TO_MOOD[emotion_lower]] += 1
            else:
                # Default mapping based on keywords
                if any(word in emotion_lower for word in ["epic", "grand", "powerful"]):
                    mood_counts[MusicMood.EPIC] += 1
                elif any(word in emotion_lower for word in ["mystery", "dark", "unknown"]):
                    mood_counts[MusicMood.MYSTERIOUS] += 1
                elif any(word in emotion_lower for word in ["happy", "joy", "hope", "inspiring"]):
                    mood_counts[MusicMood.UPLIFTING] += 1
                elif any(word in emotion_lower for word in ["calm", "peace", "gentle"]):
                    mood_counts[MusicMood.CALM] += 1
        
        # Return the mood with highest count
        return max(mood_counts, key=mood_counts.get)
