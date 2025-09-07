from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
from app.models.user import User, UserProgress
from enum import Enum


class EventType(str, Enum):
    """Event types that can award points"""
    CONTENT_VIEW = "content_view"  # 10 points
    FRAMEWORK_START = "framework_start"  # 50 points  
    AI_DIALOGUE_START = "ai_dialogue_start"  # 20 points
    OUTPUT_GENERATED = "output_generated"  # 100 points
    LOGIN_STREAK = "login_streak"  # variable points
    HIGH_QUALITY_OUTPUT = "high_quality_output"  # 50 bonus points
    FIRST_LOGIN = "first_login"  # 25 points
    FRAMEWORK_COMPLETE = "framework_complete"  # 75 points
    FRAMEWORK_REVIEW = "framework_review"  # 30 points
    REVIEW_STREAK = "review_streak"  # 15 points per streak day


class PointsService:
    """Service for managing user points and progress tracking"""
    
    # Points awarded for different events
    POINTS_MAPPING = {
        EventType.CONTENT_VIEW: 10,
        EventType.FRAMEWORK_START: 50,
        EventType.AI_DIALOGUE_START: 20,
        EventType.OUTPUT_GENERATED: 100,
        EventType.HIGH_QUALITY_OUTPUT: 50,
        EventType.FIRST_LOGIN: 25,
        EventType.FRAMEWORK_COMPLETE: 75,
        EventType.FRAMEWORK_REVIEW: 30,
        # LOGIN_STREAK and REVIEW_STREAK points are calculated dynamically
    }
    
    @staticmethod
    def award_points(
        db: Session,
        user: User,
        event_type: EventType,
        entity_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        custom_points: Optional[int] = None
    ) -> int:
        """Award points to a user for a specific event"""
        
        # Calculate points based on event type
        if custom_points is not None:
            points = custom_points
        elif event_type == EventType.LOGIN_STREAK:
            # Calculate login streak points
            streak_days = metadata.get('streak_days', 1) if metadata else 1
            points = min(streak_days * 5, 150)  # Max 30 days * 5 = 150 points
        elif event_type == EventType.REVIEW_STREAK:
            # Calculate review streak points
            streak_days = metadata.get('review_streak_days', 1) if metadata else 1
            points = min(streak_days * 15, 225)  # Max 15 days * 15 = 225 points
        else:
            points = PointsService.POINTS_MAPPING.get(event_type, 0)
        
        # Check for duplicate events (prevent double awarding)
        if entity_id and event_type in [EventType.OUTPUT_GENERATED, EventType.FRAMEWORK_COMPLETE]:
            existing = db.query(UserProgress).filter(
                and_(
                    UserProgress.user_id == user.id,
                    UserProgress.event_type == event_type.value,
                    UserProgress.entity_id == entity_id
                )
            ).first()
            
            if existing:
                return 0  # Already awarded points for this entity
        
        # Create progress record
        progress = UserProgress(
            user_id=user.id,
            event_type=event_type.value,
            entity_id=entity_id,
            points_awarded=points,
            event_metadata=metadata
        )
        
        db.add(progress)
        db.commit()
        
        return points
    
    @staticmethod
    def get_user_total_points(db: Session, user: User) -> int:
        """Get total points earned by user"""
        result = db.query(func.sum(UserProgress.points_awarded)).filter(
            UserProgress.user_id == user.id
        ).scalar()
        
        return result or 0
    
    @staticmethod
    def get_user_points_by_event_type(db: Session, user: User) -> Dict[str, int]:
        """Get points breakdown by event type"""
        results = db.query(
            UserProgress.event_type,
            func.sum(UserProgress.points_awarded).label('total_points'),
            func.count(UserProgress.id).label('event_count')
        ).filter(
            UserProgress.user_id == user.id
        ).group_by(UserProgress.event_type).all()
        
        breakdown = {}
        for event_type, total_points, count in results:
            breakdown[event_type] = {
                'total_points': total_points or 0,
                'event_count': count or 0
            }
        
        return breakdown
    
    @staticmethod
    def get_recent_points_activity(
        db: Session, 
        user: User, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get recent points activity for the user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        activities = db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.created_at >= start_date
            )
        ).order_by(UserProgress.created_at.desc()).limit(50).all()
        
        return [
            {
                'event_type': activity.event_type,
                'points': activity.points_awarded,
                'created_at': activity.created_at,
                'metadata': activity.event_metadata
            }
            for activity in activities
        ]
    
    @staticmethod
    def get_daily_points_history(
        db: Session,
        user: User,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily points accumulation for charts"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily points aggregation
        results = db.query(
            func.date(UserProgress.created_at).label('date'),
            func.sum(UserProgress.points_awarded).label('daily_points')
        ).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.created_at >= start_date
            )
        ).group_by(func.date(UserProgress.created_at)).order_by('date').all()
        
        # Fill missing dates with 0 points
        date_points = {str(result.date): result.daily_points for result in results}
        
        daily_history = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            daily_history.append({
                'date': str(current_date),
                'points': date_points.get(str(current_date), 0)
            })
            current_date += timedelta(days=1)
        
        return daily_history
    
    @staticmethod
    def get_user_ranking(db: Session, user: User) -> Dict[str, Any]:
        """Get user's ranking among all users"""
        # Get all users' total points
        user_points = db.query(
            UserProgress.user_id,
            func.sum(UserProgress.points_awarded).label('total_points')
        ).group_by(UserProgress.user_id).subquery()
        
        # Count users with more points
        users_with_more_points = db.query(func.count()).filter(
            user_points.c.total_points > PointsService.get_user_total_points(db, user)
        ).scalar()
        
        # Get total number of users with points
        total_users = db.query(func.count(func.distinct(UserProgress.user_id))).scalar()
        
        rank = (users_with_more_points or 0) + 1
        
        return {
            'rank': rank,
            'total_users': total_users or 0,
            'percentile': round((1 - (rank - 1) / max(total_users, 1)) * 100, 1) if total_users > 0 else 100
        }
    
    @staticmethod
    def check_milestone_achievements(db: Session, user: User) -> List[Dict[str, Any]]:
        """Check if user has reached any point milestones"""
        total_points = PointsService.get_user_total_points(db, user)
        
        milestones = [
            {'points': 100, 'title': 'First Steps', 'description': 'Earned your first 100 points'},
            {'points': 500, 'title': 'Getting Started', 'description': 'Reached 500 points'},
            {'points': 1000, 'title': 'Point Collector', 'description': 'Accumulated 1,000 points'},
            {'points': 2500, 'title': 'Dedicated Learner', 'description': 'Earned 2,500 points'},
            {'points': 5000, 'title': 'Expert Analyst', 'description': 'Reached 5,000 points'},
            {'points': 10000, 'title': 'Master Strategist', 'description': 'Achieved 10,000 points'},
        ]
        
        achieved_milestones = []
        for milestone in milestones:
            if total_points >= milestone['points']:
                achieved_milestones.append(milestone)
        
        return achieved_milestones