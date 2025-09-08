from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, date, timedelta
from uuid import UUID
from app.models.user import User, UserProgress
from app.services.points_service import PointsService, EventType
from app.services.badge_service import BadgeService


class LoginTrackingService:
    """Service for tracking user login streaks and awarding related points/badges"""
    
    @staticmethod
    def record_login(db: Session, user: User) -> Dict[str, Any]:
        """Record a user login and calculate streak, award points and badges"""
        today = date.today()
        
        # Check if already logged in today
        today_login = db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak']),
                func.date(UserProgress.created_at) == today
            )
        ).first()
        
        if today_login:
            # Already recorded login for today
            current_streak = LoginTrackingService.get_current_streak(db, user)
            return {
                'points_awarded': 0,
                'streak_days': current_streak,
                'is_new_login': False,
                'badges_earned': []
            }
        
        # Get login history to calculate streak
        current_streak = LoginTrackingService.calculate_login_streak(db, user)
        
        # Determine if this is the user's first ever login
        is_first_login = db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak'])
            )
        ).first() is None
        
        points_awarded = 0
        event_type = EventType.FIRST_LOGIN if is_first_login else EventType.LOGIN_STREAK
        
        # Award points for login
        if is_first_login:
            points_awarded = PointsService.award_points(
                db, user, EventType.FIRST_LOGIN,
                metadata={'first_login': True}
            )
        else:
            # Award streak points (days * 5, max 150 for 30 days)
            streak_points = min(current_streak * 5, 150)
            points_awarded = PointsService.award_points(
                db, user, EventType.LOGIN_STREAK,
                metadata={'streak_days': current_streak},
                custom_points=streak_points
            )
        
        # Check for consecutive login badge
        badges_earned = []
        badge = BadgeService.check_consecutive_login_badge(db, user, current_streak)
        if badge:
            badges_earned.append(badge)
        
        return {
            'points_awarded': points_awarded,
            'streak_days': current_streak,
            'is_first_login': is_first_login,
            'is_new_login': True,
            'badges_earned': badges_earned
        }
    
    @staticmethod
    def calculate_login_streak(db: Session, user: User) -> int:
        """Calculate the current login streak for a user"""
        today = date.today()
        
        # Get all login dates in descending order
        login_dates = db.query(func.date(UserProgress.created_at)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak'])
            )
        ).distinct().order_by(func.date(UserProgress.created_at).desc()).all()
        
        if not login_dates:
            return 1  # This will be the first login
        
        # Convert to date objects
        dates = [login_date[0] for login_date in login_dates]
        
        # Add today to the list if not already there
        if today not in dates:
            dates.insert(0, today)
        
        # Calculate consecutive days
        streak = 1
        current_date = dates[0]
        
        for i in range(1, len(dates)):
            expected_date = current_date - timedelta(days=1)
            if dates[i] == expected_date:
                streak += 1
                current_date = dates[i]
            else:
                break
        
        return streak
    
    @staticmethod
    def get_current_streak(db: Session, user: User) -> int:
        """Get the current login streak without recording a new login"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Check if user logged in today or yesterday
        recent_login = db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak']),
                or_(
                    func.date(UserProgress.created_at) == today,
                    func.date(UserProgress.created_at) == yesterday
                )
            )
        ).first()
        
        if not recent_login:
            return 0  # No recent login, streak is broken
        
        # If last login was yesterday, streak continues with today's login
        # If last login was today, get the recorded streak
        return LoginTrackingService._get_recorded_streak(db, user)
    
    @staticmethod
    def _get_recorded_streak(db: Session, user: User) -> int:
        """Get the most recent recorded streak from metadata"""
        recent_streak_record = db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'login_streak'
            )
        ).order_by(UserProgress.created_at.desc()).first()
        
        if recent_streak_record and recent_streak_record.event_metadata:
            return recent_streak_record.event_metadata.get('streak_days', 1)
        
        # Count distinct login dates if no metadata available
        login_count = db.query(func.count(func.distinct(func.date(UserProgress.created_at)))).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak'])
            )
        ).scalar()
        
        return login_count or 0
    
    @staticmethod
    def get_login_history(db: Session, user: User, days: int = 30) -> Dict[str, Any]:
        """Get login history for visualization"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Get all login dates within the range
        login_dates = db.query(func.date(UserProgress.created_at)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type.in_(['first_login', 'login_streak']),
                func.date(UserProgress.created_at) >= start_date,
                func.date(UserProgress.created_at) <= end_date
            )
        ).distinct().all()
        
        logged_dates = {login_date[0] for login_date in login_dates}
        
        # Create calendar view
        calendar = []
        current_date = start_date
        
        while current_date <= end_date:
            calendar.append({
                'date': str(current_date),
                'logged_in': current_date in logged_dates,
                'is_today': current_date == end_date
            })
            current_date += timedelta(days=1)
        
        # Calculate stats
        total_days = len(calendar)
        active_days = len(logged_dates)
        current_streak = LoginTrackingService.get_current_streak(db, user)
        
        # Calculate longest streak in the period
        longest_streak = 0
        temp_streak = 0
        
        for day in calendar:
            if day['logged_in']:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        return {
            'calendar': calendar,
            'stats': {
                'total_days': total_days,
                'active_days': active_days,
                'activity_rate': round((active_days / total_days) * 100, 1),
                'current_streak': current_streak,
                'longest_streak_in_period': longest_streak
            }
        }
    
    @staticmethod
    def get_streak_milestones() -> List[Dict[str, Any]]:
        """Get streak milestone definitions"""
        return [
            {'days': 3, 'title': '3 Day Streak', 'points_per_day': 5},
            {'days': 7, 'title': '1 Week Streak', 'points_per_day': 5, 'badge': 'Consistent User'},
            {'days': 14, 'title': '2 Week Streak', 'points_per_day': 5},
            {'days': 21, 'title': '3 Week Streak', 'points_per_day': 5},
            {'days': 30, 'title': '1 Month Streak', 'points_per_day': 5, 'max_daily_points': 150}
        ]