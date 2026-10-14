"""
Bulk Video Generation API for MAK AI
Upload a CSV and generate 100+ videos automatically.

Features:
- CSV upload with topic, style, voice, duration per row
- Queue-based processing with progress tracking
- Webhook notifications for completion
- Parallel generation for efficiency
"""

import logging
import uuid
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field

from ..deps import get_current_user, check_rate_limit
from ..models import User

log = logging.getLogger("bulk")

router = APIRouter(prefix="/api/v1/bulk", tags=["Bulk Generation"])


# ============================================================================
# Models
# ============================================================================

class BulkJobStatus(BaseModel):
    """Status of a bulk generation job"""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    total_videos: int
    completed: int
    failed: int
    in_progress: int
    estimated_time_remaining: Optional[int] = None  # seconds
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str


class BulkGenerateResponse(BaseModel):
    """Response from bulk generation request"""
    success: bool
    job_id: str
    total_videos: int
    estimated_time_seconds: int
    message: str


class VideoRow(BaseModel):
    """A single video row from CSV"""
    topic: str
    style: str = "cinematic"
    voice: str = "nova"
    duration: str = "30s"
    language: str = "English"
    webhook_url: Optional[str] = None


# ============================================================================
# In-memory job storage (replace with database in production)
# ============================================================================

bulk_jobs_db: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def generate_bulk_job_id() -> str:
    """Generate unique bulk job ID"""
    return f"bulk_{uuid.uuid4().hex[:12]}"


def parse_csv(content: str) -> List[VideoRow]:
    """
    Parse CSV content into VideoRow objects.
    
    Expected CSV format:
    topic,style,voice,duration,language
    "History of Rome","cinematic","alloy","45s","English"
    "Quantum Physics","documentary","nova","60s","English"
    """
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    
    for row in reader:
        try:
            video = VideoRow(
                topic=row.get("topic", "").strip(),
                style=row.get("style", "cinematic").strip(),
                voice=row.get("voice", "nova").strip(),
                duration=row.get("duration", "30s").strip(),
                language=row.get("language", "English").strip(),
                webhook_url=row.get("webhook_url", "").strip() or None
            )
            
            if video.topic:  # Skip empty rows
                rows.append(video)
        except Exception as e:
            log.warning(f"Skipping invalid row: {e}")
            continue
    
    return rows


async def process_bulk_job(job_id: str, videos: List[VideoRow]):
    """
    Background task to process bulk video generation.
    Generates videos one by one and updates job status.
    """
    log.info(f"🎬 Starting bulk job {job_id} with {len(videos)} videos")
    
    job = bulk_jobs_db[job_id]
    if job.get("status") == "cancelled":
        return
    job["status"] = "processing"
    job["updated_at"] = datetime.utcnow().isoformat()
    
    for i, video in enumerate(videos):
        if job.get("status") == "cancelled":
            return
        try:
            log.info(f"📹 Processing video {i+1}/{len(videos)}: {video.topic[:50]}...")
            
            job["in_progress"] = 1
            job["updated_at"] = datetime.utcnow().isoformat()
            
            # Import video engine
            try:
                from video_engine.engine import VideoEngine
                
                engine = VideoEngine()
                import asyncio
                video_path = await asyncio.to_thread(engine.generate_video,
                    topic=video.topic,
                    language=video.language,
                    duration=video.duration
                )
                
                result = {
                    "index": i,
                    "topic": video.topic,
                    "status": "completed",
                    "video_path": str(video_path),
                    "video_url": f"/videos/{Path(str(video_path)).name}"
                }
                
            except Exception as e:
                log.error(f"Generation failed for video {i+1}: {e}")
                result = {
                    "index": i,
                    "topic": video.topic,
                    "status": "failed",
                    "error": "Video generation failed; inspect local logs"
                }
                job["failed"] += 1
                job["errors"].append(result)
            
            if result.get("status") == "completed":
                job["completed"] += 1
                job["results"].append(result)
            
            job["in_progress"] = 0
            job["updated_at"] = datetime.utcnow().isoformat()
            
            # Update estimated time
            avg_time_per_video = 120  # seconds
            remaining = len(videos) - (i + 1)
            job["estimated_time_remaining"] = remaining * avg_time_per_video
            
        except Exception as e:
            log.error(f"Error processing video {i+1}: {e}")
            job["failed"] += 1
            job["errors"].append({
                "index": i,
                "topic": video.topic if video else "unknown",
                "error": "Video generation failed; inspect local logs"
            })
    
    # Mark job as complete
    job["status"] = "completed" if job["failed"] == 0 else "completed_with_errors"
    job["in_progress"] = 0
    job["estimated_time_remaining"] = 0
    job["updated_at"] = datetime.utcnow().isoformat()
    
    log.info(
        f"✅ Bulk job {job_id} completed: "
        f"{job['completed']} succeeded, {job['failed']} failed"
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate", response_model=BulkGenerateResponse)
async def bulk_generate(
    file: UploadFile = File(..., description="CSV file with video configurations"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(check_rate_limit)
):
    """
    Upload a CSV file to generate multiple videos.
    
    **CSV Format:**
    ```csv
    topic,style,voice,duration,language
    "History of Rome","cinematic","alloy","45s","English"
    "Quantum Physics","documentary","nova","60s","English"
    "The Solar System","epic","shimmer","30s","English"
    ```
    
    **Columns:**
    - `topic` (required): Video topic or script
    - `style` (optional): cinematic, documentary, minimal, neon, gradient
    - `voice` (optional): alloy, echo, fable, onyx, nova, shimmer
    - `duration` (optional): 30s, 45s, 60s
    - `language` (optional): English, Spanish, French, etc.
    
    **Returns:**
    - `job_id`: Unique identifier to track progress
    - Poll `/api/v1/bulk/status/{job_id}` for updates
    """
    # Fail closed until a persistent per-video quota reservation is implemented.
    # The prototype loop is retained for offline engineering, never paid API dispatch.
    raise HTTPException(status_code=503, detail="Bulk dispatch disabled pending persistent quota reservations")
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be a CSV file"
        )
    
    # Read and parse CSV
    try:
        content = await file.read()
        content_str = content.decode("utf-8")
        videos = parse_csv(content_str)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {str(e)}"
        )
    
    if not videos:
        raise HTTPException(
            status_code=400,
            detail="CSV is empty or has no valid rows"
        )
    
    if len(videos) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 videos per bulk job. Please split your CSV."
        )
    
    # Create job
    job_id = generate_bulk_job_id()
    now = datetime.utcnow().isoformat()
    
    bulk_jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_videos": len(videos),
        "completed": 0,
        "failed": 0,
        "in_progress": 0,
        "estimated_time_remaining": len(videos) * 120,
        "results": [],
        "errors": [],
        "created_at": now,
        "updated_at": now
    }
    
    # Start background processing
    background_tasks.add_task(process_bulk_job, job_id, videos)
    
    log.info(f"📋 Created bulk job {job_id} with {len(videos)} videos")
    
    return BulkGenerateResponse(
        success=True,
        job_id=job_id,
        total_videos=len(videos),
        estimated_time_seconds=len(videos) * 120,
        message=f"Bulk generation started for {len(videos)} videos. Poll status for updates."
    )


@router.get("/status/{job_id}", response_model=BulkJobStatus)
async def get_bulk_status(job_id: str, current_user: User = Depends(get_current_user)):
    """
    Check the status of a bulk generation job.
    
    **Status values:**
    - `pending` - Job queued
    - `processing` - Videos being generated
    - `completed` - All videos finished successfully
    - `completed_with_errors` - Some videos failed
    - `failed` - Job failed completely
    """
    if job_id not in bulk_jobs_db:
        raise HTTPException(status_code=404, detail=f"Bulk job {job_id} not found")
    
    job = bulk_jobs_db[job_id]
    if job.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    
    return BulkJobStatus(
        job_id=job["job_id"],
        status=job["status"],
        total_videos=job["total_videos"],
        completed=job["completed"],
        failed=job["failed"],
        in_progress=job["in_progress"],
        estimated_time_remaining=job.get("estimated_time_remaining"),
        results=job.get("results", []),
        errors=job.get("errors", []),
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )


@router.get("/jobs")
async def list_bulk_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """List recent bulk generation jobs"""
    jobs = [j for j in bulk_jobs_db.values() if j.get("user_id") == current_user.id or current_user.is_admin]
    
    # Filter by status if provided
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Limit results
    jobs = jobs[:limit]
    
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "total_videos": j["total_videos"],
                "completed": j["completed"],
                "failed": j["failed"],
                "created_at": j["created_at"]
            }
            for j in jobs
        ]
    }


@router.delete("/{job_id}")
async def cancel_bulk_job(job_id: str, current_user: User = Depends(get_current_user)):
    """
    Cancel a pending or processing bulk job.
    Videos already generated will be kept.
    """
    if job_id not in bulk_jobs_db:
        raise HTTPException(status_code=404, detail=f"Bulk job {job_id} not found")
    
    job = bulk_jobs_db[job_id]
    if job.get("user_id") != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    
    if job["status"] in ["completed", "completed_with_errors", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    job["status"] = "cancelled"
    job["updated_at"] = datetime.utcnow().isoformat()
    
    log.info(f"❌ Bulk job {job_id} cancelled")
    
    return {"success": True, "message": f"Bulk job {job_id} cancelled"}


@router.get("/template")
async def get_csv_template():
    """
    Get a sample CSV template for bulk generation.
    Download this and fill in your video topics.
    """
    template = """topic,style,voice,duration,language
"The History of Ancient Rome","cinematic","alloy","45s","English"
"How Quantum Computing Works","documentary","nova","60s","English"
"Top 10 Travel Destinations 2024","upbeat","shimmer","30s","English"
"The Future of AI Technology","mysterious","echo","45s","English"
"Beautiful Nature Documentary","calm","fable","60s","English"
"""
    
    return {
        "template": template,
        "columns": {
            "topic": "Video topic or full script (required)",
            "style": "Visual style: cinematic, documentary, minimal, neon, gradient",
            "voice": "TTS voice: alloy, echo, fable, onyx, nova, shimmer",
            "duration": "Video length: 30s, 45s, 60s",
            "language": "Narration language: English, Spanish, French, etc."
        },
        "example_download_url": "/api/v1/bulk/template.csv"
    }


@router.get("/template.csv")
async def download_csv_template():
    """Download the CSV template file"""
    from fastapi.responses import Response
    
    template = """topic,style,voice,duration,language
"The History of Ancient Rome","cinematic","alloy","45s","English"
"How Quantum Computing Works","documentary","nova","60s","English"
"Top 10 Travel Destinations 2024","upbeat","shimmer","30s","English"
"The Future of AI Technology","mysterious","echo","45s","English"
"Beautiful Nature Documentary","calm","fable","60s","English"
"""
    
    return Response(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bulk_template.csv"}
    )
