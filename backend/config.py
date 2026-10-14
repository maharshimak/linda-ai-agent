"""
Backend Configuration Module
Centralized Pydantic settings for all environment variables.
"""
import os
from pathlib import Path
from typing import Optional, List, Literal
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # =========================================================================
    # Primary API Keys
    # =========================================================================
    allow_public_signup: bool = False
    openai_api_key: str
    pexels_api_key: Optional[str] = None
    
    # Multi-Model API Keys (for intelligent routing)
    anthropic_api_key: Optional[str] = None      # Claude - superior storytelling
    gemini_api_key: Optional[str] = None         # Google Gemini - multimodal
    google_api_key: Optional[str] = None         # Alternative Gemini key
    mistral_api_key: Optional[str] = None        # Mistral - fast & cheap
    replicate_api_key: Optional[str] = None      # For video generation
    elevenlabs_api_key: Optional[str] = None     # Voice cloning
    deepl_api_key: Optional[str] = None          # Translation
    
    # =========================================================================
    # OpenAI Models
    # =========================================================================
    openai_script_model: str = "gpt-4o"
    openai_tts_model: str = "tts-1-hd"
    openai_tts_voice: str = "nova"
    openai_image_model: str = "dall-e-3"
    
    # =========================================================================
    # Multi-Model Routing Configuration
    # =========================================================================
    # Enable intelligent model routing (uses cheapest model for task)
    enable_model_routing: bool = True
    
    # Default models for specific tasks (when routing is enabled)
    default_script_model: str = "claude-3-5-sonnet"      # Best for stories
    default_vision_model: str = "gemini-pro"             # Best for visual
    default_fact_model: str = "gemini-pro"               # Grounded in search
    default_bulk_model: str = "mistral-small"            # Cost-effective
    
    # Cost optimization settings
    max_cost_per_video: float = 0.50                     # Max $ per video
    enable_cost_optimization: bool = True
    fallback_to_openai: bool = True                      # Use OpenAI if others fail
    
    # =========================================================================
    # Server Config
    # =========================================================================
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    # =========================================================================
    # Paths
    # =========================================================================
    output_dir: Path = Path("out")
    assets_dir: Path = Path("assets")
    sfx_dir: Path = Path("assets/sfx")
    bgm_dir: Path = Path("assets/bgm")
    luts_dir: Path = Path("assets/luts")
    
    # =========================================================================
    # Video Config
    # =========================================================================
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 60
    
    # =========================================================================
    # Audio Mastering
    # =========================================================================
    target_loudness_i: str = "-14"
    target_loudness_tp: str = "-1.0"
    target_loudness_lra: str = "7"
    
    # =========================================================================
    # Fonts (Windows)
    # =========================================================================
    windows_font: str = r"C:\Windows\Fonts\arial.ttf"
    windows_font_bold: str = r"C:\Windows\Fonts\arialbd.ttf"
    
    # =========================================================================
    # FFmpeg
    # =========================================================================
    ffmpeg_local: Optional[str] = None
    ffprobe_local: Optional[str] = None
    
    # =========================================================================
    # Authentication
    # =========================================================================
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # =========================================================================
    # Rate Limiting
    # =========================================================================
    daily_video_limit: int = 2
    
    # =========================================================================
    # Feature Flags (Ultra-Enhanced Features)
    # =========================================================================
    enable_ai_director: bool = True           # AI-powered creative decisions
    enable_smart_transitions: bool = True     # Emotion-based transitions
    enable_hook_analyzer: bool = True         # Viral hook scoring
    enable_ab_testing: bool = True            # Multi-variant generation
    enable_zapier_integration: bool = False    # External integrations
    
    # =========================================================================
    # A/B Testing Configuration
    # =========================================================================
    ab_test_variants: int = 3                 # Number of variants to generate
    ab_test_parallel: bool = True             # Generate in parallel
    
    # =========================================================================
    # Webhook Configuration
    # =========================================================================
    webhook_timeout: int = 30                 # Seconds
    webhook_retry_count: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Convenience exports
settings = get_settings()
