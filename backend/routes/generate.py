"""
Video Generation Routes
Endpoints for video creation with AI creative intelligence.
Requires authentication and enforces daily rate limits.

MAGIC MODE (DEFAULT):
User provides ONLY topic → AI handles EVERYTHING
- Auto-selects best style
- Auto-picks optimal duration
- Auto-chooses perfect voice
- Zero decisions = higher conversion

"We don't sell tools. We sell finished videos."
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db, async_session
from ..models import User, VideoGeneration
from ..deps import get_current_user, check_rate_limit, get_user_video_count_today

log = logging.getLogger("backend.generate")
router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════

class MagicGenerateRequest(BaseModel):
    """
    MAGIC MODE REQUEST - The Default Experience
    
    User provides ONLY the topic.
    AI automatically decides everything else.
    This is the primary endpoint for most users.
    """
    topic: str = Field(..., min_length=1, max_length=2000, description="What should we make a video about?")


class MagicGenerateResponse(BaseModel):
    """Magic Mode response with auto-selected parameters"""
    status: str
    job_id: str
    message: str
    auto_selected: dict  # Shows what AI chose
    estimated_time: int  # seconds
    videos_remaining: int


class SceneSpec(BaseModel):
    """Individual scene specification."""
    text: str = Field(min_length=1, max_length=1000)
    emotion: Optional[str] = "neutral"
    camera_move: Optional[str] = "dolly_in"
    duration: Optional[float] = None


class GenerateRequest(BaseModel):
    """
    ADVANCED Video generation request.
    For power users who want control.
    Most users should use /magic endpoint instead.
    """
    topic: str = Field(..., min_length=1, max_length=2000, description="Video topic or script")
    language: str = Field(default="English", description="Narration language")
    duration: str = Field(default="30s", pattern=r"^(15|30|45|60)s$", description="Target duration")
    style: Optional[str] = Field(default="cinematic", description="Visual style")
    emotion: Optional[str] = Field(default=None, description="Overall emotional tone")
    scenes: Optional[List[SceneSpec]] = Field(default=None, max_length=24, description="Manual scene breakdown")
    
    # Advanced options
    voice: Optional[str] = Field(default="nova", description="TTS voice (nova, alloy, echo, onyx, shimmer, fable)")
    videoType: Optional[str] = Field(default="General", description="Video genre/type")
    camera_style: Optional[str] = Field(default=None, description="Camera movement style")
    color_palette: Optional[str] = Field(default=None, description="Color grading preset")
    
    # Enhancement toggles (Phase 1)
    enableCaptions: Optional[bool] = Field(default=True, description="Enable word-by-word captions")
    enableMusic: Optional[bool] = Field(default=True, description="Enable background music")
    enableStockFootage: Optional[bool] = Field(default=False, description="Use stock footage instead of AI images")


class GenerateResponse(BaseModel):
    """Video generation response."""
    status: str
    job_id: Optional[str] = None
    video_path: Optional[str] = None
    preview_path: Optional[str] = None
    message: str = ""
    progress: int = 0
    videos_remaining: int = 0


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str  # queued, processing, rendering, complete, failed
    progress: int
    current_step: str
    video_path: Optional[str] = None
    error: Optional[str] = None
    api_usage: Optional[dict] = None  # API usage tracking


# ═══════════════════════════════════════════════════════════════
# Magic Mode AI Selection
# ═══════════════════════════════════════════════════════════════

def auto_select_parameters(topic: str) -> dict:
    """
    AI automatically selects optimal parameters based on topic.
    This is what makes Magic Mode magic.
    """
    topic_lower = topic.lower()
    
    # Determine best duration
    if len(topic.split()) < 10:
        duration = "30s"  # Short topic = short video
    elif len(topic.split()) < 30:
        duration = "45s"  # Medium topic
    else:
        duration = "60s"  # Long topic or full script
    
    # Determine best style
    if any(word in topic_lower for word in ["history", "documentary", "ancient", "war", "empire"]):
        style = "cinematic"
        voice = "onyx"  # Authoritative
    elif any(word in topic_lower for word in ["tech", "ai", "future", "innovation", "startup"]):
        style = "neon"
        voice = "nova"  # Modern
    elif any(word in topic_lower for word in ["nature", "travel", "beautiful", "calm", "peace"]):
        style = "earthy"
        voice = "shimmer"  # Gentle
    elif any(word in topic_lower for word in ["news", "breaking", "update", "report"]):
        style = "minimal"
        voice = "alloy"  # Neutral
    elif any(word in topic_lower for word in ["horror", "mystery", "dark", "secret"]):
        style = "noir"
        voice = "echo"  # Mysterious
    else:
        style = "cinematic"
        voice = "nova"  # Default
    
    # Determine language (future: could auto-detect)
    language = "English"
    
    return {
        "style": style,
        "voice": voice,
        "duration": duration,
        "language": language,
        "enableCaptions": True,
        "enableMusic": True,
        "reason": f"AI selected {style} style with {voice} voice based on topic analysis"
    }


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

# Simple in-memory job store (in production use Redis/DB)
jobs: Dict[str, dict] = {}


def run_pipeline_task(job_id: str, topic: str, user_id: int, video_gen_id: int):
    """Background task wrapper."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Starting pipeline..."
        
        # Add project root to path
        import sys
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        from cinematic_pipeline import create_cinematic_video
        
        # Import API usage tracker
        try:
            from api_usage_tracker import get_usage_summary
        except ImportError:
            get_usage_summary = lambda: {}
        
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Generating script & audio..."
        
        # Define callback to update job status
        def update_progress(pct, msg):
            jobs[job_id]["progress"] = pct
            jobs[job_id]["message"] = msg
        
        # Run pipeline with callback
        output_path = create_cinematic_video(topic, progress_callback=update_progress)
        
        filename = output_path.name
        
        # Get API usage summary
        api_usage = get_usage_summary()
        
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["video_path"] = f"/out/{filename}"
        jobs[job_id]["message"] = "Video generated successfully"
        jobs[job_id]["api_usage"] = api_usage
        
        # Update database record
        import asyncio
        async def update_db():
            async with async_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(VideoGeneration).where(VideoGeneration.id == video_gen_id)
                )
                video_gen = result.scalar_one_or_none()
                if video_gen:
                    video_gen.status = "complete"
                    video_gen.video_path = f"/out/{filename}"
                    video_gen.completed_at = datetime.utcnow()
                    video_gen.api_cost_usd = api_usage.get("estimated_cost_usd", 0)
                    await db.commit()
        
        asyncio.run(update_db())
        
        # Log usage
        log.info(f"API Usage: {api_usage}")
        
    except Exception as e:
        log.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "Generation failed; inspect local logs"
        
        # Update database record
        import asyncio
        async def update_db_failed():
            async with async_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(VideoGeneration).where(VideoGeneration.id == video_gen_id)
                )
                video_gen = result.scalar_one_or_none()
                if video_gen:
                    video_gen.status = "failed"
                    video_gen.error_message = str(e)
                    await db.commit()
        
        asyncio.run(update_db_failed())


# ═══════════════════════════════════════════════════════════════
# 🪄 MAGIC MODE - The Default Experience (Recommended)
# ═══════════════════════════════════════════════════════════════

@router.post("/magic", response_model=MagicGenerateResponse)
async def magic_generate(
    request: MagicGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    """
    🪄 MAGIC MODE - The Obsession Engine
    
    **This is THE endpoint most users should use.**
    
    Just provide the topic. AI handles EVERYTHING:
    - Automatically selects best visual style
    - Picks optimal duration (30s, 45s, 60s)
    - Chooses perfect voice for content type
    - Decides music mood and pacing
    
    **Example:**
    ```
    POST /api/v1/magic
    {"topic": "The rise and fall of the Roman Empire"}
    ```
    
    Result: A cinematic 45-second documentary-style video
    with authoritative voiceover and epic music.
    
    No decisions. No friction. Just results.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # 🪄 AI auto-selects optimal parameters
    auto_params = auto_select_parameters(request.topic)
    
    # Create database record
    video_gen = VideoGeneration(
        user_id=current_user.id,
        job_id=job_id,
        topic=request.topic,
        language=auto_params["language"],
        duration=auto_params["duration"],
        style=auto_params["style"],
        status="queued"
    )
    db.add(video_gen)
    await db.commit()
    await db.refresh(video_gen)
    
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "topic": request.topic,
        "message": "🪄 Magic Mode activated...",
        "user_id": current_user.id,
        "auto_selected": auto_params,
        "mode": "magic"
    }
    
    # Start background generation
    background_tasks.add_task(
        run_pipeline_task, 
        job_id, 
        request.topic, 
        current_user.id, 
        video_gen.id
    )
    
    # Calculate remaining videos
    videos_today = await get_user_video_count_today(current_user.id, db)
    videos_remaining = max(0, settings.daily_video_limit - videos_today) if not current_user.is_admin else 999
    
    log.info(f"🪄 Magic Mode: {current_user.email} → {auto_params['style']} style, {auto_params['duration']}")
    
    return MagicGenerateResponse(
        status="queued",
        job_id=job_id,
        message=f"🪄 Creating your {auto_params['duration']} {auto_params['style']} video...",
        auto_selected=auto_params,
        estimated_time=120,  # 2 minutes
        videos_remaining=videos_remaining
    )


# ═══════════════════════════════════════════════════════════════
# Advanced Generation (For Power Users)
# ═══════════════════════════════════════════════════════════════

@router.post("/generate", response_model=GenerateResponse)
async def generate_video(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_rate_limit),
    db: AsyncSession = Depends(get_db)
):
    """
    ⚙️ ADVANCED MODE - Full Control
    
    For power users who want to customize every detail.
    Most users should use the /magic endpoint instead.
    
    Start video generation in BACKGROUND (async).
    Returns job_id immediately to prevent timeout.
    Requires authentication and enforces daily limit.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Create database record
    video_gen = VideoGeneration(
        user_id=current_user.id,
        job_id=job_id,
        topic=request.topic,
        language=request.language,
        duration=request.duration,
        style=request.style or "cinematic",
        status="queued"
    )
    db.add(video_gen)
    await db.commit()
    await db.refresh(video_gen)
    
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "topic": request.topic,
        "message": "Job queued",
        "user_id": current_user.id,
        "mode": "advanced"
    }
    
    background_tasks.add_task(run_pipeline_task, job_id, request.topic, current_user.id, video_gen.id)
    
    # Calculate remaining videos
    videos_today = await get_user_video_count_today(current_user.id, db)
    videos_remaining = max(0, settings.daily_video_limit - videos_today) if not current_user.is_admin else 999
    
    log.info(f"⚙️ Advanced Mode: {current_user.email} started generation (job: {job_id})")
    
    return GenerateResponse(
        status="queued",
        job_id=job_id,
        message="Video generation started in background",
        progress=0,
        videos_remaining=videos_remaining
    )


@router.get("/generate/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    """Get status of a generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Check ownership (admins can see all)
    if not current_user.is_admin and job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")
        
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_step=job.get("message", "processing"),
        video_path=job.get("video_path"),
        error=job.get("error"),
        api_usage=job.get("api_usage")
    )


@router.get("/my-videos")
async def get_my_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's video history."""
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(VideoGeneration)
        .where(VideoGeneration.user_id == current_user.id)
        .order_by(desc(VideoGeneration.created_at))
        .limit(20)
    )
    videos = result.scalars().all()
    
    videos_today = await get_user_video_count_today(current_user.id, db)
    
    return {
        "videos": [
            {
                "id": v.id,
                "job_id": v.job_id,
                "topic": v.topic,
                "style": v.style,
                "status": v.status,
                "video_path": v.video_path,
                "created_at": v.created_at.isoformat()
            }
            for v in videos
        ],
        "videos_today": videos_today,
        "daily_limit": settings.daily_video_limit,
        "videos_remaining": max(0, settings.daily_video_limit - videos_today) if not current_user.is_admin else 999
    }


@router.get("/styles")
async def list_styles():
    """List available visual styles."""
    return {
        "styles": [
            {"id": "cinematic", "name": "Cinematic", "description": "Hollywood blockbuster look"},
            {"id": "noir", "name": "Film Noir", "description": "Dark, moody, high contrast"},
            {"id": "neon", "name": "Neon", "description": "Vibrant cyberpunk aesthetic"},
            {"id": "earthy", "name": "Earthy", "description": "Warm, natural tones"},
            {"id": "minimal", "name": "Minimal", "description": "Clean, modern, simple"}
        ]
    }


@router.get("/voices")
async def list_voices():
    """List available TTS voices."""
    return {
        "voices": [
            {"id": "nova", "name": "Nova", "description": "Warm, expressive female voice"},
            {"id": "alloy", "name": "Alloy", "description": "Neutral, professional"},
            {"id": "echo", "name": "Echo", "description": "Natural male voice"},
            {"id": "fable", "name": "Fable", "description": "British accent"},
            {"id": "onyx", "name": "Onyx", "description": "Deep, authoritative male"},
            {"id": "shimmer", "name": "Shimmer", "description": "Soft, gentle female"}
        ]
    }


@router.get("/languages")
async def list_languages():
    """List supported languages."""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "French"},
            {"code": "hi", "name": "Hindi"},
            {"code": "gu", "name": "Gujarati"}
        ]
    }
