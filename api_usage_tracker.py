# API Usage Tracker for Video Generation
# Tracks all API calls and estimates costs

from dataclasses import dataclass, field
from typing import Dict, List
import json

@dataclass
class APIUsage:
    """Track API usage for a single video generation."""
    
    # OpenAI
    script_tokens: int = 0
    tts_characters: int = 0
    image_generations: int = 0
    search_query_tokens: int = 0
    
    # Pexels
    pexels_searches: int = 0
    pexels_downloads: int = 0
    
    # Tracking lists
    calls: List[Dict] = field(default_factory=list)
    
    def log_call(self, service: str, endpoint: str, units: int, details: str = ""):
        """Log an API call."""
        self.calls.append({
            "service": service,
            "endpoint": endpoint,
            "units": units,
            "details": details
        })
    
    def log_openai_script(self, tokens: int):
        """Log script generation tokens."""
        self.script_tokens += tokens
        self.log_call("openai", "chat/completions", tokens, "Script generation")
    
    def log_openai_tts(self, characters: int):
        """Log TTS character usage."""
        self.tts_characters += characters
        self.log_call("openai", "audio/speech", characters, f"TTS: {characters} chars")
    
    def log_openai_image(self):
        """Log image generation."""
        self.image_generations += 1
        self.log_call("openai", "images/generations", 1, "DALL-E 3 image")
    
    def log_openai_search_query(self, tokens: int):
        """Log search query generation tokens."""
        self.search_query_tokens += tokens
        self.log_call("openai", "chat/completions", tokens, "Search query generation")
    
    def log_pexels_search(self):
        """Log Pexels search."""
        self.pexels_searches += 1
        self.log_call("pexels", "videos/search", 1, "Video search")
    
    def log_pexels_download(self):
        """Log Pexels download."""
        self.pexels_downloads += 1
        self.log_call("pexels", "download", 1, "Video download")
    
    def estimate_cost(self) -> Dict[str, float]:
        """Estimate costs based on OpenAI pricing (approximate)."""
        # Pricing as of 2024 (approximate)
        costs = {
            "script_generation": self.script_tokens * 0.00001,  # ~$0.01/1K tokens
            "tts": self.tts_characters * 0.000015,  # ~$15/1M chars
            "images": self.image_generations * 0.04,  # ~$0.04/image DALL-E 3
            "search_queries": self.search_query_tokens * 0.000001,  # mini model
            "pexels": 0.0,  # Free API
        }
        costs["total"] = sum(costs.values())
        return costs
    
    def summary(self) -> Dict:
        """Return usage summary."""
        costs = self.estimate_cost()
        return {
            "openai": {
                "script_tokens": self.script_tokens,
                "tts_characters": self.tts_characters,
                "image_generations": self.image_generations,
                "search_query_tokens": self.search_query_tokens,
            },
            "pexels": {
                "searches": self.pexels_searches,
                "downloads": self.pexels_downloads,
            },
            "estimated_cost_usd": round(costs["total"], 4),
            "cost_breakdown": {k: round(v, 4) for k, v in costs.items()},
        }
    
    def __str__(self) -> str:
        summary = self.summary()
        return f"""
╔══════════════════════════════════════════╗
║          API USAGE REPORT                ║
╠══════════════════════════════════════════╣
║ OPENAI:                                  ║
║   Script tokens:      {summary['openai']['script_tokens']:>10}        ║
║   TTS characters:     {summary['openai']['tts_characters']:>10}        ║
║   Image generations:  {summary['openai']['image_generations']:>10}        ║
║   Search query tokens:{summary['openai']['search_query_tokens']:>10}        ║
╠══════════════════════════════════════════╣
║ PEXELS (FREE):                           ║
║   Searches:           {summary['pexels']['searches']:>10}        ║
║   Downloads:          {summary['pexels']['downloads']:>10}        ║
╠══════════════════════════════════════════╣
║ ESTIMATED COST:       ${summary['estimated_cost_usd']:>10.4f}      ║
╚══════════════════════════════════════════╝
"""


# Global tracker instance for current generation
_current_tracker: APIUsage = None

def get_tracker() -> APIUsage:
    """Get or create the current API usage tracker."""
    global _current_tracker
    if _current_tracker is None:
        _current_tracker = APIUsage()
    return _current_tracker

def reset_tracker() -> APIUsage:
    """Reset tracker for new generation and return it."""
    global _current_tracker
    _current_tracker = APIUsage()
    return _current_tracker

def get_usage_summary() -> Dict:
    """Get usage summary for current generation."""
    return get_tracker().summary()
