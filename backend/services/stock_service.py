"""
Stock Video Service - Pexels & Pixabay Integration
Searches for and downloads royalty-free stock videos.
"""
import httpx
import asyncio
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import logging
import re

log = logging.getLogger(__name__)


@dataclass
class StockVideo:
    """Represents a stock video result."""
    id: str
    url: str
    preview_url: str
    duration: float
    width: int
    height: int
    source: str
    
    @property
    def is_vertical(self) -> bool:
        return self.height > self.width


class StockVideoService:
    """
    Stock video service that:
    - Searches Pexels API for matching videos
    - Downloads videos for use in pipeline
    - Caches results for efficiency
    """
    
    PEXELS_API = "https://api.pexels.com/videos"
    
    def __init__(self, pexels_key: str, cache_dir: str = "assets/stock_cache"):
        self.pexels_key = pexels_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        log.info("📹 StockVideoService initialized")
    
    async def search(
        self, 
        query: str, 
        orientation: str = "portrait",
        min_duration: int = 5,
        max_duration: int = 30,
        per_page: int = 10
    ) -> List[StockVideo]:
        """
        Search Pexels for videos matching the query.
        
        Args:
            query: Search keywords
            orientation: 'portrait', 'landscape', or 'square'
            min_duration: Minimum video length in seconds
            max_duration: Maximum video length in seconds
            per_page: Number of results
            
        Returns:
            List of StockVideo objects
        """
        if not self.pexels_key:
            log.warning("📹 Pexels API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.PEXELS_API}/search",
                    headers={"Authorization": self.pexels_key},
                    params={
                        "query": query,
                        "orientation": orientation,
                        "per_page": per_page,
                        "size": "medium"
                    }
                )
                
                if response.status_code != 200:
                    log.error(f"📹 Pexels API error: {response.status_code}")
                    return []
                
                data = response.json()
                videos = []
                
                for v in data.get("videos", []):
                    # Filter by duration
                    if not (min_duration <= v["duration"] <= max_duration):
                        continue
                    
                    # Get best quality video file
                    video_files = v.get("video_files", [])
                    if not video_files:
                        continue
                    
                    # Prefer HD quality
                    best_file = max(video_files, key=lambda x: x.get("height", 0))
                    
                    videos.append(StockVideo(
                        id=str(v["id"]),
                        url=best_file["link"],
                        preview_url=v.get("image", ""),
                        duration=v["duration"],
                        width=v["width"],
                        height=v["height"],
                        source="pexels"
                    ))
                
                log.info(f"📹 Found {len(videos)} videos for '{query}'")
                return videos
                
        except Exception as e:
            log.error(f"📹 Stock video search failed: {e}")
            return []
    
    async def download(self, video: StockVideo, filename: Optional[str] = None) -> Optional[Path]:
        """
        Download a stock video to the cache directory.
        
        Args:
            video: StockVideo to download
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file or None on failure
        """
        if not filename:
            filename = f"{video.source}_{video.id}.mp4"
        
        output_path = self.cache_dir / filename
        
        # Check cache first
        if output_path.exists():
            log.info(f"📹 Using cached: {output_path.name}")
            return output_path
        
        try:
            log.info(f"📹 Downloading: {video.url}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(video.url, follow_redirects=True)
                
                if response.status_code == 200:
                    output_path.write_bytes(response.content)
                    log.info(f"📹 Downloaded: {output_path.name} ({len(response.content) / 1024 / 1024:.1f} MB)")
                    return output_path
                else:
                    log.error(f"📹 Download failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            log.error(f"📹 Download error: {e}")
            return None
    
    def extract_keywords(self, text: str, max_keywords: int = 3) -> List[str]:
        """
        Extract search keywords from scene text.
        Removes common words and returns most relevant terms.
        """
        # Common words to ignore
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into", "through",
            "during", "before", "after", "above", "below", "between", "under",
            "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because", "until",
            "while", "this", "that", "these", "those", "it", "its", "we", "they"
        }
        
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stopwords and get unique
        keywords = []
        seen = set()
        for word in words:
            if word not in stopwords and word not in seen:
                seen.add(word)
                keywords.append(word)
                if len(keywords) >= max_keywords:
                    break
        
        return keywords
    
    async def get_video_for_scene(
        self, 
        scene_text: str,
        style: str = "cinematic"
    ) -> Optional[StockVideo]:
        """
        Find a suitable stock video for a scene description.
        
        Args:
            scene_text: The scene narration/description
            style: Video style preference
            
        Returns:
            Best matching StockVideo or None
        """
        keywords = self.extract_keywords(scene_text)
        
        if not keywords:
            return None
        
        # Search with combined keywords
        query = " ".join(keywords)
        videos = await self.search(query, orientation="portrait")
        
        if videos:
            # Return first (best) match
            return videos[0]
        
        # Try individual keywords as fallback
        for keyword in keywords:
            videos = await self.search(keyword, orientation="portrait")
            if videos:
                return videos[0]
        
        return None


# Factory function
def create_stock_service(pexels_key: str) -> StockVideoService:
    """Create a stock video service instance."""
    return StockVideoService(pexels_key)
