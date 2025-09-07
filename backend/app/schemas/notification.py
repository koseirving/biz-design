from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ReminderFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class NotificationPreferencesBase(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    reminder_settings: Optional[Dict[str, Any]] = Field(
        default={
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


class NotificationPreferencesCreate(NotificationPreferencesBase):
    pass


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    reminder_settings: Optional[Dict[str, Any]] = None


class NotificationPreferences(NotificationPreferencesBase):
    id: str
    user_id: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationHistoryBase(BaseModel):
    notification_type: str
    delivery_channel: str
    content: Dict[str, Any]
    scheduled_at: datetime


class NotificationHistory(NotificationHistoryBase):
    id: str
    user_id: str
    sent_at: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    total_sent: int
    total_pending: int
    recent_notifications: List[Dict[str, Any]]


class BulkNotificationRequest(BaseModel):
    notification_type: str
    delivery_channels: List[str]
    content: Dict[str, Any]
    user_filters: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    priority: str = "normal"


class NotificationTemplateBase(BaseModel):
    name: str
    notification_type: str
    delivery_channel: str
    subject_template: Optional[str] = None
    content_template: str
    variables: List[str] = Field(default_factory=list)


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplate(NotificationTemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReviewReminderSettings(BaseModel):
    enabled: bool = True
    frequency: ReminderFrequency = ReminderFrequency.DAILY
    time_of_day: str = "09:00"  # HH:MM format
    days_of_week: List[int] = Field(default=[1, 2, 3, 4, 5])  # Monday=1, Sunday=7
    reminder_intervals: List[int] = Field(default=[1, 3, 7, 30])  # days after completion


class QuietHoursSettings(BaseModel):
    enabled: bool = True
    start_time: str = "22:00"  # HH:MM format
    end_time: str = "08:00"    # HH:MM format
    timezone: str = "UTC"


class UserNotificationPreferences(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True
    review_reminders: ReviewReminderSettings = Field(default_factory=ReviewReminderSettings)
    achievement_notifications: bool = True
    weekly_summary: bool = True
    streak_notifications: bool = True
    quiet_hours: QuietHoursSettings = Field(default_factory=QuietHoursSettings)
    marketing_emails: bool = False
    product_updates: bool = True