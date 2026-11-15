from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.mentor import Mentor


def _require_db(db: Optional[AsyncSession]) -> AsyncSession:
    """Raise a clean 503 if no database is configured."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. This feature will be available once a database is connected.",
        )
    return db


async def get_current_user(
    request: Request,
    db: Optional[AsyncSession] = Depends(get_db),
) -> User:
    db = _require_db(db)

    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user_id = int(payload["sub"])
    res = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or disabled.",
        )
    return user


async def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["student", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student privileges required.")
    return current_user


async def get_current_student_profile(
    current_user: User = Depends(require_student),
    db: Optional[AsyncSession] = Depends(get_db),
) -> StudentProfile:
    db = _require_db(db)
    res = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = res.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=current_user.id, full_name=current_user.username, weekly_study_hours=8)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return current_user


async def require_mentor(
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_db),
) -> Mentor:
    db = _require_db(db)
    if current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mentor privileges required.")
    res = await db.execute(select(Mentor).where(Mentor.user_id == current_user.id))
    mentor = res.scalar_one_or_none()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mentor profile not found.")
    return mentor


async def require_mentor_or_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["student", "mentor", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")
    return current_user


async def get_mentor_for_user(
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_db),
) -> Optional[Mentor]:
    if db is None or current_user.role not in ["mentor", "admin"]:
        return None
    res = await db.execute(select(Mentor).where(Mentor.user_id == current_user.id))
    return res.scalar_one_or_none()
