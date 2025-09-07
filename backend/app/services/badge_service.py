from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
from app.models.user import User, UserBadge, UserProgress, UserOutput, UserLearningSession
from app.services.points_service import PointsService
from enum import Enum


class BadgeType(str, Enum):
    """Available badge types"""
    BEGINNER = "beginner"
    EXPLORER = "explorer"
    EXPERT = "expert"
    CONSISTENT_USER = "consistent_user"
    HIGH_PERFORMER = "high_performer"
    AI_COLLABORATOR = "ai_collaborator"
    FRAMEWORK_MASTER = "framework_master"
    QUALITY_ANALYST = "quality_analyst"


class BadgeService:
    """Service for managing user badges and achievements"""
    
    BADGE_DEFINITIONS = {
        BadgeType.BEGINNER: {
            'name': 'Beginner',
            'description': 'Complete your first framework analysis',
            'icon': '🌱',
            'color': 'green'
        },
        BadgeType.EXPLORER: {
            'name': 'Explorer',
            'description': 'Try out 3 different frameworks',
            'icon': '🔍',
            'color': 'blue'
        },
        BadgeType.EXPERT: {
            'name': 'Expert',
            'description': 'Complete 10 framework analyses',
            'icon': '🏆',
            'color': 'gold'
        },
        BadgeType.CONSISTENT_USER: {
            'name': 'Consistent User',
            'description': 'Log in for 7 consecutive days',
            'icon': '📅',
            'color': 'purple'
        },
        BadgeType.HIGH_PERFORMER: {
            'name': 'High Performer',
            'description': 'Earn 1000 points',
            'icon': '⭐',
            'color': 'orange'
        },
        BadgeType.AI_COLLABORATOR: {
            'name': 'AI Collaborator',
            'description': 'Have 20 AI conversations',
            'icon': '🤖',
            'color': 'cyan'
        },
        BadgeType.FRAMEWORK_MASTER: {
            'name': 'Framework Master',
            'description': 'Master all available frameworks',
            'icon': '👑',
            'color': 'royal'
        },
        BadgeType.QUALITY_ANALYST: {
            'name': 'Quality Analyst',
            'description': 'Create 5 high-quality outputs (80+ AI score)',
            'icon': '💎',
            'color': 'diamond'
        }
    }
    
    @staticmethod
    def award_badge(
        db: Session,
        user: User,
        badge_type: BadgeType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UserBadge]:
        """Award a badge to a user if they don't already have it"""
        
        # Check if user already has this badge
        existing = db.query(UserBadge).filter(
            and_(
                UserBadge.user_id == user.id,
                UserBadge.badge_type == badge_type.value
            )
        ).first()
        
        if existing:
            return None  # Already has this badge
        
        badge_info = BadgeService.BADGE_DEFINITIONS.get(badge_type)
        if not badge_info:
            return None
        
        # Create new badge
        user_badge = UserBadge(
            user_id=user.id,
            badge_type=badge_type.value,
            badge_name=badge_info['name'],
            badge_data={
                'description': badge_info['description'],
                'icon': badge_info['icon'],
                'color': badge_info['color'],
                'metadata': metadata
            }
        )
        
        db.add(user_badge)
        db.commit()
        db.refresh(user_badge)
        
        return user_badge
    
    @staticmethod
    def check_and_award_badges(db: Session, user: User) -> List[UserBadge]:
        """Check all badge criteria and award eligible badges"""
        newly_awarded = []
        
        # Check Beginner Badge - Complete first framework
        framework_count = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'framework_complete'
            )
        ).scalar() or 0
        
        if framework_count >= 1:
            badge = BadgeService.award_badge(db, user, BadgeType.BEGINNER)
            if badge:
                newly_awarded.append(badge)
        
        # Check Explorer Badge - Try 3 different frameworks
        distinct_frameworks = db.query(func.count(func.distinct(UserProgress.entity_id))).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'framework_start'
            )
        ).scalar() or 0
        
        if distinct_frameworks >= 3:
            badge = BadgeService.award_badge(db, user, BadgeType.EXPLORER)
            if badge:
                newly_awarded.append(badge)
        
        # Check Expert Badge - Complete 10 frameworks
        if framework_count >= 10:
            badge = BadgeService.award_badge(db, user, BadgeType.EXPERT)
            if badge:
                newly_awarded.append(badge)
        
        # Check High Performer Badge - Earn 1000 points
        total_points = PointsService.get_user_total_points(db, user)
        if total_points >= 1000:
            badge = BadgeService.award_badge(db, user, BadgeType.HIGH_PERFORMER)
            if badge:
                newly_awarded.append(badge)
        
        # Check AI Collaborator Badge - 20 AI conversations
        ai_interactions = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'ai_dialogue_start'
            )
        ).scalar() or 0
        
        if ai_interactions >= 20:
            badge = BadgeService.award_badge(db, user, BadgeType.AI_COLLABORATOR)
            if badge:
                newly_awarded.append(badge)
        
        # Check Quality Analyst Badge - 5 high-quality outputs
        high_quality_outputs = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'high_quality_output'
            )
        ).scalar() or 0
        
        if high_quality_outputs >= 5:
            badge = BadgeService.award_badge(db, user, BadgeType.QUALITY_ANALYST)
            if badge:
                newly_awarded.append(badge)
        
        return newly_awarded
    
    @staticmethod
    def check_consecutive_login_badge(
        db: Session,
        user: User,
        current_streak: int
    ) -> Optional[UserBadge]:
        """Check and award consecutive login badge"""
        if current_streak >= 7:
            return BadgeService.award_badge(
                db, 
                user, 
                BadgeType.CONSISTENT_USER,
                {'streak_days': current_streak}
            )
        return None
    
    @staticmethod
    def get_user_badges(db: Session, user: User) -> List[UserBadge]:
        """Get all badges earned by user"""
        return db.query(UserBadge).filter(
            UserBadge.user_id == user.id
        ).order_by(UserBadge.earned_at.desc()).all()
    
    @staticmethod
    def get_badge_progress(db: Session, user: User) -> Dict[str, Any]:
        """Get progress towards earning each badge"""
        progress = {}
        
        # Framework completion progress
        framework_count = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'framework_complete'
            )
        ).scalar() or 0
        
        progress['beginner'] = {
            'current': framework_count,
            'required': 1,
            'percentage': min(100, (framework_count / 1) * 100)
        }
        
        progress['expert'] = {
            'current': framework_count,
            'required': 10,
            'percentage': min(100, (framework_count / 10) * 100)
        }
        
        # Framework variety progress
        distinct_frameworks = db.query(func.count(func.distinct(UserProgress.entity_id))).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'framework_start'
            )
        ).scalar() or 0
        
        progress['explorer'] = {
            'current': distinct_frameworks,
            'required': 3,
            'percentage': min(100, (distinct_frameworks / 3) * 100)
        }
        
        # Points progress
        total_points = PointsService.get_user_total_points(db, user)
        progress['high_performer'] = {
            'current': total_points,
            'required': 1000,
            'percentage': min(100, (total_points / 1000) * 100)
        }
        
        # AI interaction progress
        ai_interactions = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'ai_dialogue_start'
            )
        ).scalar() or 0
        
        progress['ai_collaborator'] = {
            'current': ai_interactions,
            'required': 20,
            'percentage': min(100, (ai_interactions / 20) * 100)
        }
        
        # Quality outputs progress
        high_quality_outputs = db.query(func.count(UserProgress.id)).filter(
            and_(
                UserProgress.user_id == user.id,
                UserProgress.event_type == 'high_quality_output'
            )
        ).scalar() or 0
        
        progress['quality_analyst'] = {
            'current': high_quality_outputs,
            'required': 5,
            'percentage': min(100, (high_quality_outputs / 5) * 100)
        }
        
        return progress
    
    @staticmethod
    def get_available_badges() -> Dict[str, Dict[str, Any]]:
        """Get all available badges with their definitions"""
        return BadgeService.BADGE_DEFINITIONS