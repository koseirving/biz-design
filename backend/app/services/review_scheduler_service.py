from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import User, UserOutput, UserProgress, NotificationPreferences
from app.services.notification_service import NotificationService, NotificationType, DeliveryChannel, Priority
from app.services.points_service import PointsService, EventType
from app.services.badge_service import BadgeService
import logging

logger = logging.getLogger(__name__)


class EbbinghausIntervals:
    """Ebbinghaus forgetting curve intervals for optimal review timing"""
    
    # Review intervals in days based on Ebbinghaus forgetting curve
    INTERVALS = [
        1,   # 1 day after completion
        3,   # 3 days after completion  
        7,   # 1 week after completion
        30   # 1 month after completion
    ]
    
    @classmethod
    def get_next_review_date(cls, completion_date: datetime, interval_index: int) -> datetime:
        """Calculate next review date based on interval index"""
        if interval_index >= len(cls.INTERVALS):
            return None
        
        days_to_add = cls.INTERVALS[interval_index]
        return completion_date + timedelta(days=days_to_add)
    
    @classmethod
    def get_all_review_dates(cls, completion_date: datetime) -> List[datetime]:
        """Get all review dates for a completion"""
        return [
            completion_date + timedelta(days=interval)
            for interval in cls.INTERVALS
        ]


class ReviewSchedulerService:
    """Service for managing Ebbinghaus-based review scheduling"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    def schedule_reviews_for_output(self, user: User, output: UserOutput) -> List[str]:
        """Schedule all review reminders for a completed output"""
        
        logger.info(f"Scheduling reviews for output {output.id} by user {user.id}")
        
        notification_ids = []
        completion_date = output.updated_at
        
        # Get user notification preferences
        user_prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user.id
        ).first()
        
        # Check if user has review reminders enabled
        if user_prefs and not user_prefs.reminder_settings.get('review_reminders', True):
            logger.info(f"Review reminders disabled for user {user.id}")
            return notification_ids
        
        # Determine preferred delivery channels
        delivery_channels = self._get_user_delivery_channels(user_prefs)
        
        # Schedule each review interval
        for interval_index, review_date in enumerate(EbbinghausIntervals.get_all_review_dates(completion_date)):
            
            # Skip if review date is in the past
            if review_date < datetime.utcnow():
                continue
            
            # Prepare review content
            review_content = self._prepare_review_content(user, output, interval_index)
            
            # Schedule the notification
            scheduled_ids = self.notification_service.schedule_notification(
                user_id=str(user.id),
                notification_type=NotificationType.REVIEW_REMINDER,
                delivery_channels=delivery_channels,
                content=review_content,
                scheduled_at=review_date,
                priority=Priority.NORMAL
            )
            
            notification_ids.extend(scheduled_ids)
            
            logger.info(f"Scheduled review {interval_index + 1} for {review_date} (output {output.id})")
        
        return notification_ids
    
    def schedule_daily_review_digest(self, user: User) -> Optional[str]:
        """Schedule daily review digest for user"""
        
        # Get user's preferred time for reminders
        user_prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user.id
        ).first()
        
        if not user_prefs or not user_prefs.reminder_settings.get('review_reminders', True):
            return None
        
        # Get preferred time (default to 9:00 AM)
        reminder_time = user_prefs.reminder_settings.get('reminder_time', '09:00')
        
        # Calculate next reminder time
        now = datetime.utcnow()
        next_reminder = self._get_next_reminder_datetime(now, reminder_time)
        
        # Get outputs due for review
        due_outputs = self._get_outputs_due_for_review(user)
        
        if not due_outputs:
            return None
        
        # Prepare digest content
        digest_content = self._prepare_review_digest_content(user, due_outputs)
        
        # Determine delivery channels
        delivery_channels = self._get_user_delivery_channels(user_prefs)
        
        # Schedule the notification
        notification_ids = self.notification_service.schedule_notification(
            user_id=str(user.id),
            notification_type=NotificationType.REVIEW_REMINDER,
            delivery_channels=delivery_channels,
            content=digest_content,
            scheduled_at=next_reminder,
            priority=Priority.NORMAL
        )
        
        return notification_ids[0] if notification_ids else None
    
    def process_review_completion(self, user: User, output: UserOutput, review_score: Optional[int] = None) -> Dict[str, Any]:
        """Process when user completes a review session"""
        
        logger.info(f"Processing review completion for output {output.id} by user {user.id}")
        
        # Award points for review completion
        points_awarded = PointsService.award_points(
            db=self.db,
            user=user,
            event_type=EventType.FRAMEWORK_REVIEW,
            entity_id=output.id,
            metadata={
                'review_score': review_score,
                'output_type': output.output_data.get('type', 'unknown'),
                'reviewed_at': datetime.utcnow().isoformat()
            }
        )
        
        # Check for badges
        newly_awarded_badges = BadgeService.check_and_award_badges(self.db, user)
        
        # Update output metadata to track review
        output_data = output.output_data.copy()
        if 'reviews' not in output_data:
            output_data['reviews'] = []
        
        output_data['reviews'].append({
            'reviewed_at': datetime.utcnow().isoformat(),
            'score': review_score,
            'points_awarded': points_awarded
        })
        
        output.output_data = output_data
        self.db.commit()
        
        return {
            'points_awarded': points_awarded,
            'newly_awarded_badges': [badge.badge_type for badge in newly_awarded_badges],
            'total_reviews': len(output_data['reviews']),
            'next_review_due': self._calculate_next_adaptive_review(output_data['reviews'])
        }
    
    def get_user_review_schedule(self, user: User) -> Dict[str, Any]:
        """Get user's upcoming review schedule"""
        
        # Get all user outputs
        user_outputs = self.db.query(UserOutput).filter(
            UserOutput.user_id == user.id
        ).order_by(UserOutput.updated_at.desc()).all()
        
        review_schedule = {
            'upcoming_reviews': [],
            'overdue_reviews': [],
            'completed_today': 0,
            'total_pending': 0
        }
        
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for output in user_outputs:
            # Calculate review dates
            completion_date = output.updated_at
            review_dates = EbbinghausIntervals.get_all_review_dates(completion_date)
            
            # Get existing reviews from output metadata
            existing_reviews = output.output_data.get('reviews', [])
            completed_review_count = len(existing_reviews)
            
            # Check each review interval
            for interval_index, review_date in enumerate(review_dates):
                if interval_index < completed_review_count:
                    # This review has been completed
                    if any(
                        datetime.fromisoformat(r['reviewed_at']).date() == now.date()
                        for r in existing_reviews
                    ):
                        review_schedule['completed_today'] += 1
                    continue
                
                # This review is still pending
                review_info = {
                    'output_id': str(output.id),
                    'framework_name': output.output_data.get('framework_name', 'Unknown'),
                    'output_type': output.output_data.get('type', 'unknown'),
                    'review_due': review_date.isoformat(),
                    'interval_index': interval_index,
                    'days_since_completion': (now - completion_date).days,
                    'priority': 'high' if review_date < now else 'normal'
                }
                
                if review_date < now:
                    review_schedule['overdue_reviews'].append(review_info)
                else:
                    review_schedule['upcoming_reviews'].append(review_info)
                
                review_schedule['total_pending'] += 1
                
                # Only add the next pending review for this output
                break
        
        # Sort by due date
        review_schedule['upcoming_reviews'].sort(key=lambda x: x['review_due'])
        review_schedule['overdue_reviews'].sort(key=lambda x: x['review_due'])
        
        return review_schedule
    
    def _get_outputs_due_for_review(self, user: User) -> List[UserOutput]:
        """Get outputs that are due for review"""
        
        user_outputs = self.db.query(UserOutput).filter(
            UserOutput.user_id == user.id
        ).all()
        
        due_outputs = []
        now = datetime.utcnow()
        
        for output in user_outputs:
            completion_date = output.updated_at
            review_dates = EbbinghausIntervals.get_all_review_dates(completion_date)
            
            # Get existing reviews
            existing_reviews = output.output_data.get('reviews', [])
            completed_review_count = len(existing_reviews)
            
            # Check if any review is due
            for interval_index, review_date in enumerate(review_dates):
                if interval_index < completed_review_count:
                    continue  # This review is already completed
                
                if review_date <= now:
                    due_outputs.append(output)
                break  # Only check the next due review
        
        return due_outputs
    
    def _prepare_review_content(self, user: User, output: UserOutput, interval_index: int) -> Dict[str, Any]:
        """Prepare content for review reminder notification"""
        
        framework_name = output.output_data.get('framework_name', 'Framework')
        output_type = output.output_data.get('type', 'analysis')
        interval_days = EbbinghausIntervals.INTERVALS[interval_index]
        
        return {
            'subject': f'Time to Review: {framework_name} ({output_type.title()})',
            'title': f'Review Reminder',
            'message': f"It's been {interval_days} days since you completed your {framework_name} {output_type}. Time for a review to strengthen your memory!",
            'html_content': f"""
            <h2>Review Reminder 📚</h2>
            <p>Hello {user.email.split('@')[0]},</p>
            <p>It's been <strong>{interval_days} days</strong> since you completed your <strong>{framework_name}</strong> {output_type}.</p>
            <p>Based on the Ebbinghaus forgetting curve, this is the optimal time to review and reinforce your learning.</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Why Review Now?</h3>
                <ul>
                    <li>Strengthen long-term memory retention</li>
                    <li>Identify areas that need more focus</li>
                    <li>Earn additional points and badges</li>
                </ul>
            </div>
            
            <p>Click below to review your {output_type}:</p>
            """,
            'action_url': f'/outputs/{output.id}/review',
            'action_text': 'Start Review',
            'metadata': {
                'output_id': str(output.id),
                'interval_index': interval_index,
                'interval_days': interval_days,
                'framework_name': framework_name,
                'output_type': output_type
            }
        }
    
    def _prepare_review_digest_content(self, user: User, due_outputs: List[UserOutput]) -> Dict[str, Any]:
        """Prepare content for daily review digest"""
        
        count = len(due_outputs)
        
        return {
            'subject': f'Daily Review Digest - {count} Item{"s" if count != 1 else ""} Ready',
            'title': 'Your Daily Review Digest',
            'message': f"You have {count} framework{'s' if count != 1 else ''} ready for review today.",
            'html_content': f"""
            <h2>Daily Review Digest 📖</h2>
            <p>Hello {user.email.split('@')[0]},</p>
            <p>You have <strong>{count}</strong> framework{'s' if count != 1 else ''} ready for review today:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                {''.join([
                    f"<div style='padding: 10px; border-bottom: 1px solid #dee2e6;'>"
                    f"<strong>{output.output_data.get('framework_name', 'Framework')}</strong> "
                    f"({output.output_data.get('type', 'analysis').title()})"
                    f"</div>"
                    for output in due_outputs
                ])}
            </div>
            
            <p>Regular reviews help you retain knowledge longer and master the frameworks more effectively.</p>
            """,
            'action_url': '/dashboard/reviews',
            'action_text': 'Start Reviews',
            'metadata': {
                'output_count': count,
                'output_ids': [str(o.id) for o in due_outputs]
            }
        }
    
    def _get_user_delivery_channels(self, user_prefs: Optional[NotificationPreferences]) -> List[DeliveryChannel]:
        """Get user's preferred delivery channels"""
        
        channels = []
        
        if not user_prefs:
            return [DeliveryChannel.EMAIL, DeliveryChannel.IN_APP]
        
        if user_prefs.email_enabled:
            channels.append(DeliveryChannel.EMAIL)
        
        if user_prefs.push_enabled:
            channels.append(DeliveryChannel.PUSH)
        
        # Always include in-app notifications
        channels.append(DeliveryChannel.IN_APP)
        
        return list(set(channels))  # Remove duplicates
    
    def _get_next_reminder_datetime(self, current_time: datetime, reminder_time_str: str) -> datetime:
        """Calculate next reminder datetime"""
        
        try:
            hour, minute = map(int, reminder_time_str.split(':'))
            
            # Create reminder time for today
            reminder_today = current_time.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            
            # If reminder time has passed today, schedule for tomorrow
            if reminder_today <= current_time:
                reminder_today += timedelta(days=1)
            
            return reminder_today
            
        except (ValueError, AttributeError):
            # Default to 9:00 AM tomorrow if parsing fails
            return (current_time + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
    
    def _calculate_next_adaptive_review(self, review_history: List[Dict[str, Any]]) -> Optional[str]:
        """Calculate next adaptive review date based on performance"""
        
        if not review_history:
            return None
        
        # Simple adaptive logic - could be enhanced with ML
        recent_scores = [r.get('score', 50) for r in review_history[-3:]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        # Adjust interval based on performance
        if avg_score >= 80:
            # Good performance - extend interval
            next_review = datetime.utcnow() + timedelta(days=14)
        elif avg_score >= 60:
            # Average performance - standard interval
            next_review = datetime.utcnow() + timedelta(days=7)
        else:
            # Poor performance - shorter interval
            next_review = datetime.utcnow() + timedelta(days=3)
        
        return next_review.isoformat()