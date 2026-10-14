# stock_videos.py — Pexels Video API Integration
# Free, high-quality, watermark-free stock videos

import os
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("stock-video")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"


class StockVideoFetcher:
    """Fetch free HD stock videos from Pexels."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or PEXELS_API_KEY
        if not self.api_key:
            log.warning("PEXELS_API_KEY not set - stock videos disabled")
        
    def search_video(self, query: str, orientation: str = "portrait", 
                     min_duration: int = 5, max_duration: int = 30) -> Optional[str]:
        """
        Search for a stock video matching the query.
        Returns URL to HD video file, or None if not found.
        
        Args:
            query: Search term (e.g., "sunset ocean waves")
            orientation: "portrait" for 9:16, "landscape" for 16:9
            min_duration: Minimum video length in seconds
            max_duration: Maximum video length in seconds
        """
        if not self.api_key:
            return None
            
        try:
            headers = {"Authorization": self.api_key}
            params = {
                "query": query,
                "orientation": orientation,
                "per_page": 10,
                "size": "medium"  # medium = good quality, not too large
            }
            
            log.info(f"🎥 Searching Pexels: '{query}'...")
            response = requests.get(PEXELS_VIDEO_SEARCH_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("videos", [])
            
            if not videos:
                log.warning(f"   No videos found for '{query}'")
                return None
            
            # Find best matching video by duration
            for video in videos:
                duration = video.get("duration", 0)
                if min_duration <= duration <= max_duration:
                    # Get HD video file URL
                    video_files = video.get("video_files", [])
                    hd_url = self._get_best_quality_url(video_files, orientation)
                    if hd_url:
                        log.info(f"   ✅ Found: {duration}s video")
                        return hd_url
            
            # Fallback: just use first video
            video_files = videos[0].get("video_files", [])
            return self._get_best_quality_url(video_files, orientation)
            
        except Exception as e:
            log.error(f"   ❌ Pexels search failed: {e}")
            return None
    
    def _get_best_quality_url(self, video_files: List[Dict], orientation: str) -> Optional[str]:
        """Get the best quality video URL for the orientation."""
        if not video_files:
            return None
        
        # Sort by quality (height for portrait, width for landscape)
        if orientation == "portrait":
            # For 9:16, we want tall videos
            sorted_files = sorted(video_files, key=lambda x: x.get("height", 0), reverse=True)
        else:
            sorted_files = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
        
        # Get HD (720p-1080p) - not 4K (too large)
        for vf in sorted_files:
            height = vf.get("height", 0)
            if 720 <= height <= 1920:
                return vf.get("link")
        
        # Fallback to first available
        return sorted_files[0].get("link") if sorted_files else None
    
    def download_video(self, url: str, output_path: Path) -> Optional[Path]:
        """Download video from URL to local file."""
        try:
            log.info(f"   ⬇️ Downloading video...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            log.info(f"   ✅ Saved: {output_path.name}")
            return output_path
            
        except Exception as e:
            log.error(f"   ❌ Download failed: {e}")
            return None
    
    def get_video_for_scene(self, scene_text: str, emotion: str, 
                            output_path: Path, duration: int = 10) -> Optional[Path]:
        """
        Get a stock video matching the scene description.
        Uses GPT to generate optimal search query.
        """
        # Generate search query from scene text
        # Simple keyword extraction for now
        keywords = self._extract_keywords(scene_text, emotion)
        
        # Search Pexels
        video_url = self.search_video(
            query=keywords,
            orientation="portrait",
            min_duration=3,
            max_duration=30
        )
        
        if not video_url:
            return None
        
        # Download
        return self.download_video(video_url, output_path)
    
    def _extract_keywords(self, text: str, emotion: str) -> str:
        """Extract search keywords from scene text."""
        # Emotion to visual mapping
        emotion_keywords = {
            "epic": "cinematic dramatic",
            "calm": "peaceful serene nature",
            "intense": "action fast motion",
            "mysterious": "dark fog shadow",
            "uplifting": "sunrise hope light",
            "neutral": "professional business"
        }
        
        base = emotion_keywords.get(emotion, "cinematic")
        
        # Extract nouns/key concepts from text (simple approach)
        # In production, would use NLP or GPT
        words = text.lower().split()
        visual_words = []
        
        # Common visual keywords to look for
        visual_hints = [
            "ocean", "mountain", "city", "forest", "sky", "sun", "moon",
            "people", "crowd", "technology", "nature", "space", "stars",
            "water", "fire", "earth", "wind", "storm", "rain", "snow",
            "building", "road", "journey", "travel", "future", "past",
            "night", "day", "morning", "evening", "sunset", "sunrise"
        ]
        
        for word in words:
            if word in visual_hints:
                visual_words.append(word)
        
        if visual_words:
            return f"{base} {' '.join(visual_words[:3])}"
        
        return base


# Global instance
_fetcher = None

def get_stock_video_fetcher() -> StockVideoFetcher:
    """Get or create the stock video fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = StockVideoFetcher()
    return _fetcher


def fetch_stock_video(query: str, output_path: Path, 
                      orientation: str = "portrait") -> Optional[Path]:
    """Convenience function to fetch a stock video."""
    fetcher = get_stock_video_fetcher()
    url = fetcher.search_video(query, orientation=orientation)
    if url:
        return fetcher.download_video(url, output_path)
    return None


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    fetcher = StockVideoFetcher()
    
    result = fetcher.search_video("epic cinematic ocean sunset", orientation="portrait")
    print(f"Found: {result}")
