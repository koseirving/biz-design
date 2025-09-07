from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.core.security import get_current_user
from app.models.user import User, NotificationPreferences, NotificationHistory
from app.schemas.notification import (
    NotificationPreferencesCreate,
    NotificationPreferencesUpdate,
    NotificationPreferences as NotificationPreferencesSchema,
    NotificationHistory as NotificationHistorySchema,
    NotificationStatsResponse,
    UserNotificationPreferences
)
from app.services.notification_service import NotificationService, NotificationType, DeliveryChannel, Priority
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferencesSchema)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences"""
    
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = NotificationPreferences(
            user_id=current_user.id,
            email_enabled=True,
            push_enabled=True,
            reminder_settings={
                "review_reminders": True,
                "achievement_notifications": True,
                "weekly_summary": True,
                "streak_notifications": True,
                "reminder_frequency": "daily",
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
                "timezone": "UTC"
            }
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.post("/preferences", response_model=NotificationPreferencesSchema)
def create_notification_preferences(
    preferences: NotificationPreferencesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update user's notification preferences"""
    
    existing_prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if existing_prefs:
        # Update existing preferences
        for field, value in preferences.dict(exclude_unset=True).items():
            setattr(existing_prefs, field, value)
        db.commit()
        db.refresh(existing_prefs)
        return existing_prefs
    else:
        # Create new preferences
        new_prefs = NotificationPreferences(
            user_id=current_user.id,
            **preferences.dict()
        )
        db.add(new_prefs)
        db.commit()
        db.refresh(new_prefs)
        return new_prefs


@router.put("/preferences", response_model=NotificationPreferencesSchema)
def update_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""
    
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    update_data = preferences.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "reminder_settings" and value is not None:
            # Merge with existing reminder settings
            current_settings = prefs.reminder_settings or {}
            current_settings.update(value)
            prefs.reminder_settings = current_settings
        else:
            setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return prefs


@router.get("/history", response_model=List[NotificationHistorySchema])
def get_notification_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    notification_type: Optional[str] = Query(default=None),
    delivery_channel: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    """Get user's notification history with filtering"""
    
    query = db.query(NotificationHistory).filter(
        NotificationHistory.user_id == current_user.id
    )
    
    if notification_type:
        query = query.filter(NotificationHistory.notification_type == notification_type)
    
    if delivery_channel:
        query = query.filter(NotificationHistory.delivery_channel == delivery_channel)
    
    if status:
        query = query.filter(NotificationHistory.status == status)
    
    notifications = query.order_by(
        NotificationHistory.scheduled_at.desc()
    ).offset(offset).limit(limit).all()
    
    return notifications


@router.get("/stats", response_model=NotificationStatsResponse)
def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification statistics"""
    
    notification_service = NotificationService(db)
    stats = notification_service.get_user_notification_stats(str(current_user.id))
    
    return stats


@router.post("/test")
def send_test_notification(
    notification_type: str,
    delivery_channels: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test notification to the current user"""
    
    try:
        # Validate notification type
        NotificationType(notification_type)
        
        # Validate delivery channels
        channels = [DeliveryChannel(channel) for channel in delivery_channels]
        
        # Prepare test content
        test_content = {
            "subject": "Test Notification from Biz Design",
            "title": "Test Notification",
            "message": "This is a test notification to verify your notification settings.",
            "html_content": f"""
            <h2>Test Notification</h2>
            <p>Hello {current_user.email},</p>
            <p>This is a test notification to verify your notification settings are working correctly.</p>
            <p>Notification Type: {notification_type}</p>
            <p>Delivery Channels: {', '.join(delivery_channels)}</p>
            <p>Best regards,<br>Biz Design Team</p>
            """,
            "action_url": "/dashboard",
            "action_text": "Go to Dashboard"
        }
        
        # Send notification
        notification_service = NotificationService(db)
        notification_ids = notification_service.schedule_notification(
            user_id=str(current_user.id),
            notification_type=NotificationType(notification_type),
            delivery_channels=channels,
            content=test_content,
            priority=Priority.HIGH
        )
        
        return {
            "message": "Test notification scheduled successfully",
            "notification_ids": notification_ids,
            "channels": delivery_channels
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification type or delivery channel: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to send test notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.delete("/cancel/{notification_type}")
def cancel_notifications(
    notification_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel scheduled notifications of a specific type"""
    
    try:
        # Validate notification type
        validated_type = NotificationType(notification_type)
        
        notification_service = NotificationService(db)
        cancelled_count = notification_service.cancel_scheduled_notifications(
            user_id=str(current_user.id),
            notification_type=validated_type
        )
        
        return {
            "message": f"Cancelled {cancelled_count} notifications of type {notification_type}",
            "cancelled_count": cancelled_count
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification type: {notification_type}"
        )
    except Exception as e:
        logger.error(f"Failed to cancel notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel notifications"
        )


@router.get("/types")
def get_notification_types():
    """Get available notification types"""
    
    return {
        "notification_types": [
            {
                "value": nt.value,
                "name": nt.value.replace('_', ' ').title(),
                "description": _get_notification_description(nt)
            }
            for nt in NotificationType
        ],
        "delivery_channels": [
            {
                "value": dc.value,
                "name": dc.value.replace('_', ' ').title(),
                "description": _get_channel_description(dc)
            }
            for dc in DeliveryChannel
        ]
    }


@router.post("/preferences/quick-setup")
def quick_setup_preferences(
    preferences: UserNotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quick setup for notification preferences with predefined templates"""
    
    # Convert UserNotificationPreferences to NotificationPreferences format
    reminder_settings = {
        "review_reminders": preferences.review_reminders.enabled,
        "achievement_notifications": preferences.achievement_notifications,
        "weekly_summary": preferences.weekly_summary,
        "streak_notifications": preferences.streak_notifications,
        "reminder_frequency": preferences.review_reminders.frequency.value,
        "reminder_time": preferences.review_reminders.time_of_day,
        "reminder_days": preferences.review_reminders.days_of_week,
        "reminder_intervals": preferences.review_reminders.reminder_intervals,
        "quiet_hours_enabled": preferences.quiet_hours.enabled,
        "quiet_hours_start": preferences.quiet_hours.start_time,
        "quiet_hours_end": preferences.quiet_hours.end_time,
        "timezone": preferences.quiet_hours.timezone,
        "marketing_emails": preferences.marketing_emails,
        "product_updates": preferences.product_updates
    }
    
    # Check for existing preferences
    existing_prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if existing_prefs:
        # Update existing preferences
        existing_prefs.email_enabled = preferences.email_enabled
        existing_prefs.push_enabled = preferences.push_enabled
        existing_prefs.reminder_settings = reminder_settings
        db.commit()
        db.refresh(existing_prefs)
        return existing_prefs
    else:
        # Create new preferences
        new_prefs = NotificationPreferences(
            user_id=current_user.id,
            email_enabled=preferences.email_enabled,
            push_enabled=preferences.push_enabled,
            reminder_settings=reminder_settings
        )
        db.add(new_prefs)
        db.commit()
        db.refresh(new_prefs)
        return new_prefs


def _get_notification_description(notification_type: NotificationType) -> str:
    """Get description for notification type"""
    descriptions = {
        NotificationType.REVIEW_REMINDER: "Reminders to review completed frameworks",
        NotificationType.ACHIEVEMENT_UNLOCK: "Notifications when you unlock achievements",
        NotificationType.BADGE_EARNED: "Notifications when you earn new badges",
        NotificationType.STREAK_MILESTONE: "Notifications for login streak milestones",
        NotificationType.FRAMEWORK_COMPLETION: "Notifications when you complete frameworks",
        NotificationType.WEEKLY_SUMMARY: "Weekly summary of your learning progress",
        NotificationType.SUBSCRIPTION_RENEWAL: "Subscription renewal reminders",
        NotificationType.WELCOME_SERIES: "Welcome series for new users"
    }
    return descriptions.get(notification_type, "General notification")


def _get_channel_description(channel: DeliveryChannel) -> str:
    """Get description for delivery channel"""
    descriptions = {
        DeliveryChannel.EMAIL: "Email notifications to your registered email address",
        DeliveryChannel.PUSH: "Push notifications to your device",
        DeliveryChannel.IN_APP: "Notifications within the application"
    }
    return descriptions.get(channel, "Notification channel")