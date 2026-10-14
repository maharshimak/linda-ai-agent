"""
Backend Application Entry Point
FastAPI server with CORS, routes, and static file serving.
"""
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select

from .config import settings
from .database import init_db, async_session
from .models import User, VideoGeneration
from .deps import get_password_hash, get_current_user
from .routes import generate, health, auth, admin, bulk


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="🎬 %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("backend")


async def create_admin_if_not_exists():
    """Optional explicit bootstrap; never create an account from shipped credentials."""
    email = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "")
    if not email and not password:
        log.info("Administrator bootstrap is disabled")
        return
    if not email or len(password) < 12:
        raise RuntimeError("Explicit bootstrap email and a password of at least 12 characters are required")
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is None:
            db.add(User(email=email, password_hash=get_password_hash(password), is_admin=True))
            await db.commit()
            log.info("Explicit administrator bootstrap completed")



async def create_asset_directories():
    """Create required asset directories."""
    directories = [
        settings.output_dir,
        settings.assets_dir,
        settings.sfx_dir,
        settings.bgm_dir,
        settings.luts_dir,
        Path("out/variants")  # For A/B test variants
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    log.info(f"📁 Asset directories created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    log.info("🚀 Starting MAK AI Ultra-Enhanced Video Platform")
    log.info(f"   Output directory: {settings.output_dir.absolute()}")
    
    # Create directories
    await create_asset_directories()
    
    # Initialize database
    await init_db()
    log.info("📦 Database initialized")
    
    # Create admin user
    await create_admin_if_not_exists()
    
    # Log enabled features
    features = []
    if settings.enable_ai_director:
        features.append("AI Director")
    if settings.enable_smart_transitions:
        features.append("Smart Transitions")
    if settings.enable_hook_analyzer:
        features.append("Hook Analyzer")
    if settings.enable_ab_testing:
        features.append("A/B Testing")
    if settings.enable_zapier_integration:
        features.append("Zapier Integration")
    
    log.info(f"✨ Enabled features: {', '.join(features)}")
    
    yield
    
    # Shutdown
    log.info("👋 Shutting down backend")


# Create FastAPI app
app = FastAPI(
    title="Cinematic video development backend",
    description="Authenticated development API and source for video generation. Rendering requires separate provider and asset setup.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

@app.middleware("http")
async def bounded_body(request: Request, call_next):
    size=0
    chunks=[]
    async for chunk in request.stream():
        size+=len(chunk)
        if size>32000:
            return JSONResponse({"detail":"Request body exceeds 32 KB"},status_code=413)
        chunks.append(chunk)
    request._body=b"".join(chunks)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Cache-Control"]="no-store"
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(generate.router, prefix="/api/v1", tags=["Generation"])

# Integration and TrendJack prototypes are not mounted. They lack user-scoped
# authorization and validated webhook destinations; no flag enables them.
app.include_router(bulk.router, tags=["Bulk Generation"])


@app.get("/out/{filename}")
@app.get("/videos/{filename}")
async def owned_media(filename: str, current_user: User = Depends(get_current_user)):
    """Authenticated files only; no static directory bypass exists."""
    if Path(filename).name != filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Media not found")
    root=settings.output_dir.resolve()
    target=(root/filename).resolve()
    if target.parent != root or not target.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    async with async_session() as db:
        result=await db.execute(select(VideoGeneration).where(VideoGeneration.video_path == f"/out/{filename}"))
        records=result.scalars().all()
    if not any(record.user_id == current_user.id for record in records) and not current_user.is_admin:
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(target, media_type="video/mp4")


# Root redirect for convenience
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Cinematic video development backend",
        "version": "3.0.0",
        "status": "online",
        "docs": "/docs",
        "features": {
            "ai_director": settings.enable_ai_director,
            "smart_transitions": settings.enable_smart_transitions,
            "hook_analyzer": settings.enable_hook_analyzer,
            "ab_testing": settings.enable_ab_testing,
            "zapier_integration": False,
            "multi_model_routing": settings.enable_model_routing
        },
        "endpoints": {
            "health": "/health",
            "generate": "/api/v1/generate",
            "auth": "/api/v1/auth",
            "admin": "/api/v1/admin"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
