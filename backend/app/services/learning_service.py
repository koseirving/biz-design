from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.user import UserLearningSession, UserProgress, BusinessFramework
from datetime import datetime, timedelta
import uuid


class LearningSessionService:
    
    @staticmethod
    def start_session(
        db: Session,
        user_id: str,
        framework_id: str,
        learning_data: Optional[Dict[str, Any]] = None
    ) -> UserLearningSession:
        """Start a new learning session"""
        # End any existing incomplete session for this framework
        existing_session = db.query(UserLearningSession).filter(
            UserLearningSession.user_id == user_id,
            UserLearningSession.framework_id == framework_id,
            UserLearningSession.status == 'in_progress'
        ).first()
        
        if existing_session:
            existing_session.status = 'abandoned'
            existing_session.completed_at = datetime.utcnow()
        
        # Create new session
        session = UserLearningSession(
            id=uuid.uuid4(),
            user_id=user_id,
            framework_id=framework_id,
            started_at=datetime.utcnow(),
            learning_data=learning_data or {},
            status='in_progress'
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Record progress event
        ProgressService.record_event(
            db=db,
            user_id=user_id,
            event_type='SESSION_STARTED',
            entity_id=framework_id,
            points_awarded=20,
            metadata={'session_id': str(session.id)}
        )
        
        return session
    
    @staticmethod
    def update_session_progress(
        db: Session,
        session_id: str,
        user_id: str,
        progress_data: Dict[str, Any]
    ) -> Optional[UserLearningSession]:
        """Update session progress"""
        session = db.query(UserLearningSession).filter(
            UserLearningSession.id == session_id,
            UserLearningSession.user_id == user_id,
            UserLearningSession.status == 'in_progress'
        ).first()
        
        if not session:
            return None
        
        # Merge progress data
        if session.learning_data:
            session.learning_data.update(progress_data)
        else:
            session.learning_data = progress_data
        
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def complete_session(
        db: Session,
        session_id: str,
        user_id: str,
        final_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UserLearningSession]:
        """Complete a learning session"""
        session = db.query(UserLearningSession).filter(
            UserLearningSession.id == session_id,
            UserLearningSession.user_id == user_id,
            UserLearningSession.status == 'in_progress'
        ).first()
        
        if not session:
            return None
        
        session.status = 'completed'
        session.completed_at = datetime.utcnow()
        
        if final_data:
            if session.learning_data:
                session.learning_data.update(final_data)
            else:
                session.learning_data = final_data
        
        db.commit()
        db.refresh(session)
        
        # Record completion event
        duration = (session.completed_at - session.started_at).total_seconds() / 60  # minutes
        ProgressService.record_event(
            db=db,
            user_id=user_id,
            event_type='SESSION_COMPLETED',
            entity_id=session.framework_id,
            points_awarded=50,
            metadata={
                'session_id': str(session.id),
                'duration_minutes': duration,
                'completion_data': final_data
            }
        )
        
        return session
    
    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: str,
        framework_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserLearningSession]:
        """Get user's learning sessions"""
        query = db.query(UserLearningSession).filter(
            UserLearningSession.user_id == user_id
        )
        
        if framework_id:
            query = query.filter(UserLearningSession.framework_id == framework_id)
        
        if status:
            query = query.filter(UserLearningSession.status == status)
        
        return query.order_by(desc(UserLearningSession.started_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_session(db: Session, session_id: str, user_id: str) -> Optional[UserLearningSession]:
        """Get a specific session"""
        return db.query(UserLearningSession).filter(
            UserLearningSession.id == session_id,
            UserLearningSession.user_id == user_id
        ).first()
    
    @staticmethod
    def get_active_session(db: Session, user_id: str, framework_id: str) -> Optional[UserLearningSession]:
        """Get active session for a framework"""
        return db.query(UserLearningSession).filter(
            UserLearningSession.user_id == user_id,
            UserLearningSession.framework_id == framework_id,
            UserLearningSession.status == 'in_progress'
        ).first()


class ProgressService:
    
    @staticmethod
    def record_event(
        db: Session,
        user_id: str,
        event_type: str,
        entity_id: Optional[str] = None,
        points_awarded: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserProgress:
        """Record a progress event"""
        progress = UserProgress(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            entity_id=entity_id,
            points_awarded=points_awarded,
            event_metadata=metadata or {}
        )
        
        db.add(progress)
        db.commit()
        db.refresh(progress)
        return progress
    
    @staticmethod
    def get_user_progress(
        db: Session,
        user_id: str,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserProgress]:
        """Get user's progress events"""
        query = db.query(UserProgress).filter(UserProgress.user_id == user_id)
        
        if event_type:
            query = query.filter(UserProgress.event_type == event_type)
        
        return query.order_by(desc(UserProgress.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_total_points(db: Session, user_id: str) -> int:
        """Get user's total points"""
        result = db.query(func.sum(UserProgress.points_awarded)).filter(
            UserProgress.user_id == user_id
        ).scalar()
        
        return result or 0
    
    @staticmethod
    def get_framework_completion_count(db: Session, user_id: str) -> int:
        """Get number of completed frameworks"""
        return db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.event_type == 'SESSION_COMPLETED'
        ).count()
    
    @staticmethod
    def get_ai_interaction_count(db: Session, user_id: str) -> int:
        """Get number of AI interactions"""
        return db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.event_type == 'AI_INTERACTION'
        ).count()


class LearningAnalyticsService:
    
    @staticmethod
    def get_user_analytics(db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning analytics for a user"""
        # Basic stats
        total_points = ProgressService.get_total_points(db, user_id)
        frameworks_completed = ProgressService.get_framework_completion_count(db, user_id)
        ai_interactions = ProgressService.get_ai_interaction_count(db, user_id)
        
        # Learning time analysis
        completed_sessions = db.query(UserLearningSession).filter(
            UserLearningSession.user_id == user_id,
            UserLearningSession.status == 'completed'
        ).all()
        
        total_learning_time = 0
        session_durations = []
        
        for session in completed_sessions:
            if session.completed_at and session.started_at:
                duration = (session.completed_at - session.started_at).total_seconds() / 60
                total_learning_time += duration
                session_durations.append(duration)
        
        avg_session_time = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Framework analysis
        framework_stats = db.query(
            BusinessFramework.name,
            BusinessFramework.category,
            func.count(UserLearningSession.id).label('sessions_count'),
            func.avg(
                func.extract('epoch', UserLearningSession.completed_at - UserLearningSession.started_at) / 60
            ).label('avg_duration')
        ).join(
            UserLearningSession, BusinessFramework.id == UserLearningSession.framework_id
        ).filter(
            UserLearningSession.user_id == user_id,
            UserLearningSession.status == 'completed'
        ).group_by(BusinessFramework.id, BusinessFramework.name, BusinessFramework.category).all()
        
        # Recent activity
        recent_progress = ProgressService.get_user_progress(db, user_id, limit=10)
        
        # Learning streak
        learning_streak = LearningAnalyticsService._calculate_learning_streak(db, user_id)
        
        return {
            "total_points": total_points,
            "frameworks_completed": frameworks_completed,
            "ai_interactions": ai_interactions,
            "total_learning_time_minutes": total_learning_time,
            "average_session_time_minutes": avg_session_time,
            "learning_streak_days": learning_streak,
            "framework_stats": [
                {
                    "name": stat.name,
                    "category": stat.category,
                    "sessions_completed": stat.sessions_count,
                    "average_duration_minutes": float(stat.avg_duration or 0)
                }
                for stat in framework_stats
            ],
            "recent_activities": [
                {
                    "event_type": progress.event_type,
                    "points_awarded": progress.points_awarded,
                    "created_at": progress.created_at.isoformat(),
                    "metadata": progress.event_metadata
                }
                for progress in recent_progress
            ]
        }
    
    @staticmethod
    def _calculate_learning_streak(db: Session, user_id: str) -> int:
        """Calculate current learning streak in days"""
        # Get distinct days when user had learning activity
        learning_days = db.query(
            func.date(UserProgress.created_at)
        ).filter(
            UserProgress.user_id == user_id,
            UserProgress.event_type.in_(['SESSION_STARTED', 'SESSION_COMPLETED'])
        ).distinct().order_by(desc(func.date(UserProgress.created_at))).all()
        
        if not learning_days:
            return 0
        
        streak = 0
        current_date = datetime.utcnow().date()
        
        for day_tuple in learning_days:
            day = day_tuple[0]
            if day == current_date or day == current_date - timedelta(days=streak + 1):
                streak += 1
                current_date = day
            else:
                break
        
        return streak
    
    @staticmethod
    def get_weekly_progress(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get weekly learning progress"""
        # Get last 7 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=6)
        
        daily_stats = db.query(
            func.date(UserProgress.created_at).label('date'),
            func.sum(UserProgress.points_awarded).label('points'),
            func.count(UserProgress.id).label('activities')
        ).filter(
            UserProgress.user_id == user_id,
            func.date(UserProgress.created_at) >= start_date,
            func.date(UserProgress.created_at) <= end_date
        ).group_by(func.date(UserProgress.created_at)).all()
        
        # Fill in missing days
        result = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            stats = next((s for s in daily_stats if s.date == date), None)
            result.append({
                "date": date.isoformat(),
                "points": int(stats.points or 0) if stats else 0,
                "activities": int(stats.activities or 0) if stats else 0
            })
        
        return result