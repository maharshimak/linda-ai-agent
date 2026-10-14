"""
Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "10x-ai-video-platform",
        "components": {
            "api": "online",
            "engine": "not verified; requires configured providers and licensed assets"
        }
    }
