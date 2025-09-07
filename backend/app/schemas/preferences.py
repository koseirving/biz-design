from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    reminder_settings: Optional[Dict[str, Any]] = None

class NotificationPreferencesResponse(BaseModel):
    id: str
    user_id: str
    email_enabled: bool
    push_enabled: bool
    reminder_settings: Optional[Dict[str, Any]]
    updated_at: datetime
    
    class Config:
        from_attributes = True