from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.progress import (
    ProgressSummary, 
    LoginHistory, 
    BadgeInfo, 
    UserRanking,
    DailyPoints,
    RecentActivity
)
from app.services.points_service import PointsService
from app.services.badge_service import BadgeService
from app.services.login_service import LoginTrackingService

router = APIRouter()


@router.get("/me/progress", response_model=ProgressSummary)
def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive user progress data"""
    
    # Get basic stats
    total_points = PointsService.get_user_total_points(db, current_user)
    points_breakdown = PointsService.get_user_points_by_event_type(db, current_user)
    ranking = PointsService.get_user_ranking(db, current_user)
    milestones = PointsService.check_milestone_achievements(db, current_user)
    
    # Get badge information
    user_badges = BadgeService.get_user_badges(db, current_user)
    badge_progress = BadgeService.get_badge_progress(db, current_user)
    
    # Get activity data
    daily_points = PointsService.get_daily_points_history(db, current_user, 30)
    recent_activity = PointsService.get_recent_points_activity(db, current_user, 7)
    
    # Get login streak
    current_streak = LoginTrackingService.get_current_streak(db, current_user)
    
    # Count various activities
    framework_events = points_breakdown.get('framework_complete', {'event_count': 0})
    ai_events = points_breakdown.get('ai_dialogue_start', {'event_count': 0})
    output_events = points_breakdown.get('output_generated', {'event_count': 0})
    
    return ProgressSummary(
        total_points=total_points,
        earned_badges=[
            BadgeInfo(
                type=badge.badge_type,
                name=badge.badge_name,
                description=badge.badge_data.get('description', ''),
                icon=badge.badge_data.get('icon', ''),
                color=badge.badge_data.get('color', ''),
                earned_at=badge.earned_at
            ) for badge in user_badges
        ],
        completed_frameworks=framework_events['event_count'],
        ai_interactions=ai_events['event_count'],
        outputs_created=output_events['event_count'],
        current_streak=current_streak,
        ranking=UserRanking(**ranking),
        badge_progress={
            badge_type: {
                'current': progress['current'],
                'required': progress['required'],
                'percentage': progress['percentage']
            } for badge_type, progress in badge_progress.items()
        },
        points_by_event={
            event_type: {
                'total_points': breakdown['total_points'],
                'event_count': breakdown['event_count']
            } for event_type, breakdown in points_breakdown.items()
        },
        daily_points=[
            DailyPoints(date=day['date'], points=day['points'])
            for day in daily_points
        ],
        recent_activity=[
            RecentActivity(
                event_type=activity['event_type'],
                points=activity['points'],
                created_at=activity['created_at'],
                metadata=activity['metadata']
            ) for activity in recent_activity
        ],
        milestones_achieved=milestones
    )


@router.get("/me/login-history", response_model=LoginHistory)
def get_login_history(
    days: int = Query(30, ge=7, le=90, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user login history and streak information"""
    return LoginHistory(**LoginTrackingService.get_login_history(db, current_user, days))


@router.get("/me/badges")
def get_user_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all badges earned by the user"""
    badges = BadgeService.get_user_badges(db, current_user)
    return {
        "earned_badges": [
            {
                "id": str(badge.id),
                "type": badge.badge_type,
                "name": badge.badge_name,
                "data": badge.badge_data,
                "earned_at": badge.earned_at
            } for badge in badges
        ]
    }


@router.get("/badges/available")
def get_available_badges():
    """Get all available badges and their requirements"""
    return {
        "badges": BadgeService.get_available_badges(),
        "milestones": LoginTrackingService.get_streak_milestones()
    }


@router.get("/me/points/history")
def get_points_history(
    days: int = Query(30, ge=7, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed points earning history"""
    daily_points = PointsService.get_daily_points_history(db, current_user, days)
    recent_activity = PointsService.get_recent_points_activity(db, current_user, days)
    
    return {
        "daily_points": daily_points,
        "recent_activity": recent_activity,
        "total_points": PointsService.get_user_total_points(db, current_user)
    }


@router.get("/me/ranking")
def get_user_ranking(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's ranking among all users"""
    return PointsService.get_user_ranking(db, current_user)


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(10, ge=5, le=100, description="Number of top users to return"),
    db: Session = Depends(get_db)
):
    """Get top users leaderboard (public data only)"""
    from sqlalchemy import func
    from app.models.user import UserProgress
    
    # Get top users by total points (without exposing personal data)
    top_users = db.query(
        UserProgress.user_id,
        func.sum(UserProgress.points_awarded).label('total_points')
    ).group_by(UserProgress.user_id).order_by(
        func.sum(UserProgress.points_awarded).desc()
    ).limit(limit).all()
    
    return {
        "leaderboard": [
            {
                "rank": index + 1,
                "user_id": str(user.user_id),
                "total_points": user.total_points,
                "is_anonymous": True  # Don't expose email or other personal data
            } for index, user in enumerate(top_users)
        ]
    }