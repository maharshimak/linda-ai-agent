"""
Admin Routes
Admin-only endpoints for user management and analytics.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import User, VideoGeneration
from ..deps import get_current_admin
from ..config import settings


log = logging.getLogger("backend.admin")
router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════

class UserSummary(BaseModel):
    id: int
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    total_videos: int
    videos_today: int


class VideoSummary(BaseModel):
    id: int
    job_id: str
    user_id: int
    user_email: str
    topic: str
    style: str
    status: str
    video_path: Optional[str]
    created_at: datetime
    api_cost_usd: Optional[float]


class AnalyticsResponse(BaseModel):
    total_users: int
    total_videos: int
    videos_today: int
    videos_this_week: int
    active_users: int
    total_api_cost: float
    recent_videos: List[VideoSummary]


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Active users (created videos in last 7 days)
    active_users_result = await db.execute(
        select(func.count(func.distinct(VideoGeneration.user_id)))
        .where(VideoGeneration.created_at >= week_start)
    )
    active_users = active_users_result.scalar() or 0
    
    # Total videos
    total_videos_result = await db.execute(select(func.count(VideoGeneration.id)))
    total_videos = total_videos_result.scalar() or 0
    
    # Videos today
    videos_today_result = await db.execute(
        select(func.count(VideoGeneration.id))
        .where(VideoGeneration.created_at >= today_start)
    )
    videos_today = videos_today_result.scalar() or 0
    
    # Videos this week
    videos_week_result = await db.execute(
        select(func.count(VideoGeneration.id))
        .where(VideoGeneration.created_at >= week_start)
    )
    videos_this_week = videos_week_result.scalar() or 0
    
    # Total API cost
    cost_result = await db.execute(
        select(func.sum(VideoGeneration.api_cost_usd))
    )
    total_api_cost = cost_result.scalar() or 0.0
    
    # Recent videos (last 10)
    recent_result = await db.execute(
        select(VideoGeneration)
        .order_by(desc(VideoGeneration.created_at))
        .limit(10)
    )
    recent_videos_db = recent_result.scalars().all()
    
    recent_videos = []
    for v in recent_videos_db:
        user_result = await db.execute(select(User).where(User.id == v.user_id))
        user = user_result.scalar_one_or_none()
        recent_videos.append(VideoSummary(
            id=v.id,
            job_id=v.job_id,
            user_id=v.user_id,
            user_email=user.email if user else "Unknown",
            topic=v.topic[:100],  # Truncate for display
            style=v.style,
            status=v.status,
            video_path=v.video_path,
            created_at=v.created_at,
            api_cost_usd=v.api_cost_usd
        ))
    
    return AnalyticsResponse(
        total_users=total_users,
        total_videos=total_videos,
        videos_today=videos_today,
        videos_this_week=videos_this_week,
        active_users=active_users,
        total_api_cost=total_api_cost,
        recent_videos=recent_videos
    )


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all users with video stats."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(User)
        .order_by(desc(User.created_at))
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    user_summaries = []
    for user in users:
        # Count total videos
        total_result = await db.execute(
            select(func.count(VideoGeneration.id))
            .where(VideoGeneration.user_id == user.id)
        )
        total_videos = total_result.scalar() or 0
        
        # Count videos today
        today_result = await db.execute(
            select(func.count(VideoGeneration.id))
            .where(VideoGeneration.user_id == user.id)
            .where(VideoGeneration.created_at >= today_start)
        )
        videos_today = today_result.scalar() or 0
        
        user_summaries.append(UserSummary(
            id=user.id,
            email=user.email,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            total_videos=total_videos,
            videos_today=videos_today
        ))
    
    return user_summaries


@router.get("/videos", response_model=List[VideoSummary])
async def list_videos(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = Query(None)
):
    """List all video generations."""
    query = select(VideoGeneration).order_by(desc(VideoGeneration.created_at))
    
    if user_id:
        query = query.where(VideoGeneration.user_id == user_id)
    
    result = await db.execute(query.offset(skip).limit(limit))
    videos = result.scalars().all()
    
    video_summaries = []
    for v in videos:
        user_result = await db.execute(select(User).where(User.id == v.user_id))
        user = user_result.scalar_one_or_none()
        video_summaries.append(VideoSummary(
            id=v.id,
            job_id=v.job_id,
            user_id=v.user_id,
            user_email=user.email if user else "Unknown",
            topic=v.topic[:100],
            style=v.style,
            status=v.status,
            video_path=v.video_path,
            created_at=v.created_at,
            api_cost_usd=v.api_cost_usd
        ))
    
    return video_summaries


@router.get("/user/{user_id}")
async def get_user_details(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user info with video history."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all videos for this user
    videos_result = await db.execute(
        select(VideoGeneration)
        .where(VideoGeneration.user_id == user_id)
        .order_by(desc(VideoGeneration.created_at))
    )
    videos = videos_result.scalars().all()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        },
        "videos": [
            {
                "id": v.id,
                "job_id": v.job_id,
                "topic": v.topic,
                "style": v.style,
                "status": v.status,
                "video_path": v.video_path,
                "created_at": v.created_at.isoformat(),
                "api_cost_usd": v.api_cost_usd
            }
            for v in videos
        ]
    }
