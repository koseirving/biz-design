from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User, NotificationPreferences
from app.schemas.preferences import NotificationPreferencesUpdate, NotificationPreferencesResponse
from datetime import datetime
import uuid

router = APIRouter(prefix="/users", tags=["preferences"])

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = NotificationPreferences(
            id=uuid.uuid4(),
            user_id=current_user.id,
            email_enabled=True,
            push_enabled=True,
            reminder_settings={
                "learning_reminders": True,
                "achievement_notifications": True,
                "review_reminders": True,
                "preferred_time": "09:00"
            },
            updated_at=datetime.utcnow()
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return NotificationPreferencesResponse(
        id=str(preferences.id),
        user_id=str(preferences.user_id),
        email_enabled=preferences.email_enabled,
        push_enabled=preferences.push_enabled,
        reminder_settings=preferences.reminder_settings,
        updated_at=preferences.updated_at
    )

@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create new preferences if none exist
        preferences = NotificationPreferences(
            id=uuid.uuid4(),
            user_id=current_user.id,
            email_enabled=True,
            push_enabled=True,
            reminder_settings={},
            updated_at=datetime.utcnow()
        )
        db.add(preferences)
    
    # Update preferences
    if preferences_update.email_enabled is not None:
        preferences.email_enabled = preferences_update.email_enabled
    
    if preferences_update.push_enabled is not None:
        preferences.push_enabled = preferences_update.push_enabled
    
    if preferences_update.reminder_settings is not None:
        preferences.reminder_settings = preferences_update.reminder_settings
    
    preferences.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(preferences)
    
    return NotificationPreferencesResponse(
        id=str(preferences.id),
        user_id=str(preferences.user_id),
        email_enabled=preferences.email_enabled,
        push_enabled=preferences.push_enabled,
        reminder_settings=preferences.reminder_settings,
        updated_at=preferences.updated_at
    )