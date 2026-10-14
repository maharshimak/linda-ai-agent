"""
Database Models
User and VideoGeneration models for authentication and tracking.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to videos
    videos: Mapped[list["VideoGeneration"]] = relationship(back_populates="user", lazy="selectin")
    
    def __repr__(self):
        return f"<User {self.email}>"


class VideoGeneration(Base):
    """Video generation tracking model."""
    __tablename__ = "video_generations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    
    # Request details
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="English")
    duration: Mapped[str] = mapped_column(String(10), default="30s")
    style: Mapped[str] = mapped_column(String(50), default="cinematic")
    
    # Result
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued, processing, complete, failed
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # API usage tracking
    api_cost_usd: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Relationship to user
    user: Mapped["User"] = relationship(back_populates="videos")
    
    def __repr__(self):
        return f"<VideoGeneration {self.job_id} by user {self.user_id}>"
