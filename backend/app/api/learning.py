from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.learning_service import (
    LearningSessionService, 
    ProgressService, 
    LearningAnalyticsService
)
from app.services.framework_service import FrameworkService
from datetime import datetime

router = APIRouter()


# Schemas
class SessionStart(BaseModel):
    framework_id: str
    learning_data: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    progress_data: Dict[str, Any]


class SessionComplete(BaseModel):
    final_data: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    framework_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    learning_data: Optional[Dict[str, Any]]
    status: str
    
    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    entity_id: Optional[str]
    points_awarded: int
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Learning session endpoints
@router.post("/sessions/start", response_model=SessionResponse)
async def start_learning_session(
    session_data: SessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new learning session"""
    # Verify framework exists and user has access
    framework = FrameworkService.get_framework_by_id(db, session_data.framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    # Check premium access
    if framework.is_premium and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required to access this framework"
        )
    
    session = LearningSessionService.start_session(
        db=db,
        user_id=str(current_user.id),
        framework_id=session_data.framework_id,
        learning_data=session_data.learning_data
    )
    
    return SessionResponse.from_orm(session)


@router.get("/sessions", response_model=List[SessionResponse])
async def get_learning_sessions(
    framework_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's learning sessions"""
    sessions = LearningSessionService.get_user_sessions(
        db=db,
        user_id=str(current_user.id),
        framework_id=framework_id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return [SessionResponse.from_orm(session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_learning_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific learning session"""
    session = LearningSessionService.get_session(db, session_id, str(current_user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse.from_orm(session)


@router.put("/sessions/{session_id}/progress", response_model=SessionResponse)
async def update_session_progress(
    session_id: str,
    update_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update session progress"""
    session = LearningSessionService.update_session_progress(
        db=db,
        session_id=session_id,
        user_id=str(current_user.id),
        progress_data=update_data.progress_data
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already completed")
    
    return SessionResponse.from_orm(session)


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
async def complete_learning_session(
    session_id: str,
    completion_data: SessionComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a learning session"""
    session = LearningSessionService.complete_session(
        db=db,
        session_id=session_id,
        user_id=str(current_user.id),
        final_data=completion_data.final_data
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already completed")
    
    return SessionResponse.from_orm(session)


@router.get("/sessions/active/{framework_id}", response_model=Optional[SessionResponse])
async def get_active_session(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active session for a framework"""
    session = LearningSessionService.get_active_session(
        db, str(current_user.id), framework_id
    )
    
    return SessionResponse.from_orm(session) if session else None


# Progress tracking endpoints
@router.get("/progress", response_model=List[ProgressResponse])
async def get_user_progress(
    event_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's progress events"""
    progress = ProgressService.get_user_progress(
        db=db,
        user_id=str(current_user.id),
        event_type=event_type,
        skip=skip,
        limit=limit
    )
    
    return [ProgressResponse.from_orm(p) for p in progress]


@router.get("/progress/points")
async def get_total_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's total points"""
    total_points = ProgressService.get_total_points(db, str(current_user.id))
    return {"total_points": total_points}


# Analytics endpoints
@router.get("/analytics")
async def get_learning_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive learning analytics"""
    analytics = LearningAnalyticsService.get_user_analytics(db, str(current_user.id))
    return analytics


@router.get("/analytics/weekly")
async def get_weekly_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weekly learning progress"""
    weekly_progress = LearningAnalyticsService.get_weekly_progress(db, str(current_user.id))
    return {"weekly_progress": weekly_progress}


# Event recording endpoint (for manual events)
@router.post("/progress/record")
async def record_progress_event(
    event_type: str,
    entity_id: Optional[str] = None,
    points_awarded: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a manual progress event"""
    progress = ProgressService.record_event(
        db=db,
        user_id=str(current_user.id),
        event_type=event_type,
        entity_id=entity_id,
        points_awarded=points_awarded,
        metadata=metadata
    )
    
    return ProgressResponse.from_orm(progress)