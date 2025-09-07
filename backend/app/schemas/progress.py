from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class DailyPoints(BaseModel):
    date: str
    points: int


class EventBreakdown(BaseModel):
    total_points: int
    event_count: int


class UserRanking(BaseModel):
    rank: int
    total_users: int
    percentile: float


class BadgeInfo(BaseModel):
    type: str
    name: str
    description: str
    icon: str
    color: str
    earned_at: datetime


class BadgeProgress(BaseModel):
    current: int
    required: int
    percentage: float


class RecentActivity(BaseModel):
    event_type: str
    points: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class LoginStats(BaseModel):
    total_days: int
    active_days: int
    activity_rate: float
    current_streak: int
    longest_streak_in_period: int


class LoginCalendarDay(BaseModel):
    date: str
    logged_in: bool
    is_today: bool


class LoginHistory(BaseModel):
    calendar: List[LoginCalendarDay]
    stats: LoginStats


class ProgressSummary(BaseModel):
    total_points: int
    earned_badges: List[BadgeInfo]
    completed_frameworks: int
    ai_interactions: int
    outputs_created: int
    current_streak: int
    ranking: UserRanking
    badge_progress: Dict[str, BadgeProgress]
    points_by_event: Dict[str, EventBreakdown]
    daily_points: List[DailyPoints]
    recent_activity: List[RecentActivity]
    milestones_achieved: List[Dict[str, Any]]