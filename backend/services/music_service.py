"""
Music Service - Background Music Selection & Mixing
Detects mood from script and selects appropriate royalty-free music.
"""
import os
import random
from pathlib import Path
from typing import Optional, List
import logging

log = logging.getLogger(__name__)

class MusicService:
    """
    Background music service that:
    - Detects mood from video script
    - Selects appropriate background music
    - Provides mixing utilities
    """
    
    # Mood keywords mapping
    MOOD_KEYWORDS = {
        "epic": [
            "war", "battle", "hero", "power", "ancient", "empire", "conquer",
            "legendary", "massive", "dramatic", "victory", "glory", "titan",
            "warrior", "kingdom", "dynasty", "revolution"
        ],
        "calm": [
            "nature", "peace", "meditation", "relax", "gentle", "soft",
            "tranquil", "serene", "quiet", "mindful", "zen", "healing",
            "sunset", "ocean", "forest", "wellness"
        ],
        "upbeat": [
            "travel", "happy", "fun", "adventure", "explore", "journey",
            "exciting", "energetic", "positive", "joyful", "celebration",
            "summer", "party", "dance", "vibrant"
        ],
        "mysterious": [
            "space", "mystery", "unknown", "dark", "secret", "hidden",
            "enigma", "puzzle", "cosmos", "universe", "deep", "alien",
            "supernatural", "paranormal", "noir"
        ],
        "emotional": [
            "love", "sad", "memory", "life", "heart", "soul", "dream",
            "nostalgic", "beautiful", "touching", "inspiring", "hope",
            "loss", "farewell", "reunion", "family"
        ],
    }
    
    # Default volume levels for different content types
    VOLUME_PRESETS = {
        "narration_heavy": 0.12,  # Quieter for lots of talking
        "visual_heavy": 0.25,    # Louder for visual content
        "balanced": 0.18,        # Default balance
        "intro_outro": 0.30,     # Louder for intros/outros
    }
    
    def __init__(self, bgm_dir: str = "assets/bgm"):
        self.bgm_dir = Path(bgm_dir)
        self.music_library = self._scan_music_library()
        log.info(f"🎵 MusicService initialized with {sum(len(v) for v in self.music_library.values())} tracks")
    
    def _scan_music_library(self) -> dict:
        """Scan the BGM directory for available music files."""
        library = {}
        
        if not self.bgm_dir.exists():
            log.warning(f"BGM directory not found: {self.bgm_dir}")
            return library
        
        for mood_folder in self.bgm_dir.iterdir():
            if mood_folder.is_dir():
                tracks = list(mood_folder.glob("*.mp3")) + list(mood_folder.glob("*.wav"))
                if tracks:
                    library[mood_folder.name] = tracks
                    log.info(f"  📁 {mood_folder.name}: {len(tracks)} tracks")
        
        return library
    
    def detect_mood(self, script: str) -> str:
        """
        Analyze script text to detect the dominant mood.
        Returns: One of 'epic', 'calm', 'upbeat', 'mysterious', 'emotional'
        """
        script_lower = script.lower()
        mood_scores = {}
        
        for mood, keywords in self.MOOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in script_lower)
            mood_scores[mood] = score
        
        # Get mood with highest score
        best_mood = max(mood_scores, key=mood_scores.get)
        best_score = mood_scores[best_mood]
        
        # Default to 'calm' if no clear mood detected
        if best_score == 0:
            log.info("🎵 No clear mood detected, defaulting to 'calm'")
            return "calm"
        
        log.info(f"🎵 Detected mood: {best_mood} (score: {best_score})")
        return best_mood
    
    def get_track(self, mood: str) -> Optional[Path]:
        """
        Get a random music track for the specified mood.
        Falls back to 'calm' if mood not available.
        """
        # Try exact mood first
        tracks = self.music_library.get(mood, [])
        
        # Fallback to calm
        if not tracks:
            tracks = self.music_library.get("calm", [])
        
        # Fallback to any available tracks
        if not tracks:
            for mood_tracks in self.music_library.values():
                if mood_tracks:
                    tracks = mood_tracks
                    break
        
        if tracks:
            selected = random.choice(tracks)
            log.info(f"🎵 Selected track: {selected.name}")
            return selected
        
        log.warning("🎵 No music tracks available")
        return None
    
    def get_volume_for_content(self, content_type: str = "balanced") -> float:
        """Get recommended volume level for content type."""
        return self.VOLUME_PRESETS.get(content_type, 0.18)
    
    def get_all_moods(self) -> List[str]:
        """Return list of available moods."""
        return list(self.MOOD_KEYWORDS.keys())
    
    def add_track(self, mood: str, file_path: Path) -> bool:
        """Add a track to the library (for runtime additions)."""
        if mood not in self.music_library:
            self.music_library[mood] = []
        
        if file_path.exists():
            self.music_library[mood].append(file_path)
            return True
        return False


# Singleton instance
_music_service: Optional[MusicService] = None

def get_music_service() -> MusicService:
    """Get or create the music service singleton."""
    global _music_service
    if _music_service is None:
        _music_service = MusicService()
    return _music_service
