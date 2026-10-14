"""
Authentication Dependencies
JWT token handling, password hashing, and access control.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .database import get_db
from .models import User, VideoGeneration
from .config import settings


# Password hashing - support both argon2 (old hashes) and bcrypt (new hashes)
# This ensures backward compatibility while using faster bcrypt for new passwords
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2"],
    deprecated=["argon2"],  # Old argon2 hashes will still verify but new ones use bcrypt
    bcrypt__rounds=10  # Faster than default 12 rounds
)

# JWT Bearer scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def check_rate_limit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Check if user has exceeded daily video generation limit."""
    # Admins bypass rate limit
    if current_user.is_admin:
        return current_user
    
    # Count videos generated today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(func.count(VideoGeneration.id))
        .where(VideoGeneration.user_id == current_user.id)
        .where(VideoGeneration.created_at >= today_start)
    )
    count = result.scalar()
    
    if count >= settings.daily_video_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {settings.daily_video_limit} videos reached. Try again tomorrow!"
        )
    
    return current_user


async def get_user_video_count_today(user_id: int, db: AsyncSession) -> int:
    """Get the number of videos a user has generated today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(func.count(VideoGeneration.id))
        .where(VideoGeneration.user_id == user_id)
        .where(VideoGeneration.created_at >= today_start)
    )
    return result.scalar() or 0
