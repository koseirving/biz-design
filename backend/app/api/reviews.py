from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.deps import get_db, get_current_user
from app.models.user import User, UserOutput
from app.schemas.notification import NotificationStatsResponse
from app.services.review_scheduler_service import ReviewSchedulerService, EbbinghausIntervals
from app.services.review_content_generator import ReviewContentGenerator, ReviewContentType
from app.services.review_progress_service import ReviewProgressService
from app.services.notification_service import NotificationService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ReviewSessionRequest(BaseModel):
    session_type: str = "mixed"  # quiz, reflection, problems, mixed
    content_types: List[str] = ["quiz", "summary", "reflection", "ai_problems"]
    scores: Dict[str, float] = {}
    time_spent_minutes: int = 0
    completion_percentage: float = 100.0
    difficulty_rating: int = 3  # 1-5 scale


class ReviewContentRequest(BaseModel):
    content_types: List[str] = ["quiz", "summary", "reflection", "ai_problems"]


@router.get("/schedule")
def get_review_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's review schedule based on Ebbinghaus intervals"""
    
    scheduler_service = ReviewSchedulerService(db)
    schedule = scheduler_service.get_user_review_schedule(current_user)
    
    return {
        'user_id': str(current_user.id),
        'schedule': schedule,
        'ebbinghaus_intervals': EbbinghausIntervals.INTERVALS
    }


@router.post("/outputs/{output_id}/schedule")
def schedule_reviews_for_output(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Schedule Ebbinghaus review reminders for a completed output"""
    
    # Get the output
    output = db.query(UserOutput).filter(
        UserOutput.id == output_id,
        UserOutput.user_id == current_user.id
    ).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found"
        )
    
    # Schedule reviews in background
    def schedule_reviews():
        scheduler_service = ReviewSchedulerService(db)
        notification_ids = scheduler_service.schedule_reviews_for_output(current_user, output)
        logger.info(f"Scheduled {len(notification_ids)} review reminders for output {output_id}")
    
    background_tasks.add_task(schedule_reviews)
    
    # Calculate review dates for response
    review_dates = EbbinghausIntervals.get_all_review_dates(output.updated_at)
    
    return {
        'message': 'Review reminders scheduled successfully',
        'output_id': output_id,
        'review_dates': [date.isoformat() for date in review_dates],
        'intervals_days': EbbinghausIntervals.INTERVALS
    }


@router.post("/outputs/{output_id}/content")
async def generate_review_content(
    output_id: str,
    request: ReviewContentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered review content for an output"""
    
    # Get the output
    output = db.query(UserOutput).filter(
        UserOutput.id == output_id,
        UserOutput.user_id == current_user.id
    ).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found"
        )
    
    try:
        content_generator = ReviewContentGenerator()
        review_content = await content_generator.generate_review_content(
            user=current_user,
            output=output,
            content_types=request.content_types
        )
        
        # Get content statistics
        stats = content_generator.get_review_content_statistics(review_content)
        
        return {
            'review_content': review_content,
            'content_statistics': stats,
            'generated_at': review_content['generated_at']
        }
        
    except Exception as e:
        logger.error(f"Failed to generate review content for output {output_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate review content"
        )


@router.post("/outputs/{output_id}/session")
def record_review_session(
    output_id: str,
    session: ReviewSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a completed review session"""
    
    # Get the output
    output = db.query(UserOutput).filter(
        UserOutput.id == output_id,
        UserOutput.user_id == current_user.id
    ).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found"
        )
    
    try:
        progress_service = ReviewProgressService(db)
        session_result = progress_service.record_review_session(
            user=current_user,
            output=output,
            session_data=session.dict()
        )
        
        return {
            'message': 'Review session recorded successfully',
            'output_id': output_id,
            'session_result': session_result
        }
        
    except Exception as e:
        logger.error(f"Failed to record review session for output {output_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record review session"
        )


@router.get("/analytics")
def get_review_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, le=365, ge=1)
):
    """Get comprehensive review analytics for the user"""
    
    progress_service = ReviewProgressService(db)
    analytics = progress_service.get_user_review_analytics(current_user, days)
    
    return {
        'user_id': str(current_user.id),
        'analytics': analytics,
        'generated_at': str(db.query(db.func.now()).scalar())
    }


@router.get("/analytics/framework/{framework_name}")
def get_framework_review_analytics(
    framework_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review analytics for a specific framework"""
    
    progress_service = ReviewProgressService(db)
    analytics = progress_service.get_framework_review_progress(current_user, framework_name)
    
    if 'error' in analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=analytics['error']
        )
    
    return {
        'user_id': str(current_user.id),
        'framework_analytics': analytics
    }


@router.get("/effectiveness")
def get_learning_effectiveness_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive learning effectiveness report"""
    
    progress_service = ReviewProgressService(db)
    effectiveness_report = progress_service.get_learning_effectiveness_report(current_user)
    
    if 'error' in effectiveness_report:
        return {
            'user_id': str(current_user.id),
            'effectiveness_report': effectiveness_report,
            'has_data': False
        }
    
    return {
        'user_id': str(current_user.id),
        'effectiveness_report': effectiveness_report,
        'has_data': True
    }


@router.get("/content-types")
def get_available_content_types():
    """Get available review content types"""
    
    return {
        'content_types': [
            {
                'type': ReviewContentType.QUIZ,
                'name': 'Quiz',
                'description': 'Multiple choice questions testing key concepts',
                'estimated_time_minutes': 5
            },
            {
                'type': ReviewContentType.SUMMARY,
                'name': 'Key Points Summary',
                'description': 'Condensed summary of main insights and takeaways',
                'estimated_time_minutes': 3
            },
            {
                'type': ReviewContentType.REFLECTION,
                'name': 'Reflection Questions',
                'description': 'Thoughtful questions for deeper understanding',
                'estimated_time_minutes': 10
            },
            {
                'type': ReviewContentType.AI_PROBLEMS,
                'name': 'Application Problems',
                'description': 'Practical scenarios to apply framework knowledge',
                'estimated_time_minutes': 15
            }
        ],
        'recommended_combinations': [
            ['quiz', 'summary'],
            ['reflection', 'ai_problems'],
            ['quiz', 'summary', 'reflection', 'ai_problems']
        ]
    }


@router.post("/daily-digest/schedule")
def schedule_daily_review_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Schedule daily review digest for the user"""
    
    def schedule_digest():
        scheduler_service = ReviewSchedulerService(db)
        notification_id = scheduler_service.schedule_daily_review_digest(current_user)
        
        if notification_id:
            logger.info(f"Scheduled daily review digest for user {current_user.id}: {notification_id}")
        else:
            logger.info(f"No review digest needed for user {current_user.id}")
    
    background_tasks.add_task(schedule_digest)
    
    return {
        'message': 'Daily review digest scheduling initiated',
        'user_id': str(current_user.id)
    }


@router.get("/outputs/{output_id}/history")
def get_output_review_history(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review history for a specific output"""
    
    # Get the output
    output = db.query(UserOutput).filter(
        UserOutput.id == output_id,
        UserOutput.user_id == current_user.id
    ).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found"
        )
    
    review_sessions = output.output_data.get('review_sessions', [])
    
    # Calculate summary statistics
    if review_sessions:
        scores = [s.get('overall_score', 0) for s in review_sessions]
        total_time = sum(s.get('time_spent_minutes', 0) for s in review_sessions)
        
        summary_stats = {
            'total_sessions': len(review_sessions),
            'average_score': round(sum(scores) / len(scores), 1),
            'best_score': max(scores),
            'latest_score': scores[-1] if scores else 0,
            'total_time_hours': round(total_time / 60, 1),
            'improvement_trend': (scores[-1] - scores[0]) if len(scores) > 1 else 0
        }
    else:
        summary_stats = {
            'total_sessions': 0,
            'average_score': 0,
            'best_score': 0,
            'latest_score': 0,
            'total_time_hours': 0,
            'improvement_trend': 0
        }
    
    return {
        'output_id': output_id,
        'framework_name': output.output_data.get('framework_name', 'Unknown'),
        'output_type': output.output_data.get('type', 'unknown'),
        'created_at': output.created_at.isoformat(),
        'review_sessions': review_sessions,
        'summary_stats': summary_stats,
        'next_recommended_review': output.output_data.get('next_review_recommended')
    }


@router.delete("/outputs/{output_id}/reminders")
def cancel_review_reminders(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel scheduled review reminders for an output"""
    
    # Get the output
    output = db.query(UserOutput).filter(
        UserOutput.id == output_id,
        UserOutput.user_id == current_user.id
    ).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output not found"
        )
    
    try:
        notification_service = NotificationService(db)
        cancelled_count = notification_service.cancel_scheduled_notifications(
            user_id=str(current_user.id),
            notification_type=None  # Cancel all notifications for this user
        )
        
        return {
            'message': f'Cancelled review reminders for output {output_id}',
            'cancelled_count': cancelled_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel review reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel review reminders"
        )


@router.post("/test-reminder")
def send_test_review_reminder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Send a test review reminder to the user"""
    
    def send_test():
        from app.services.notification_service import NotificationType, DeliveryChannel, Priority
        
        notification_service = NotificationService(db)
        
        test_content = {
            'subject': 'Test Review Reminder',
            'title': 'Test Review Reminder',
            'message': 'This is a test review reminder to verify your notification settings.',
            'html_content': f"""
            <h2>Test Review Reminder 📚</h2>
            <p>Hello {current_user.email.split('@')[0]},</p>
            <p>This is a test review reminder sent from your Biz Design learning platform.</p>
            <p>Your review notification system is working correctly!</p>
            """,
            'action_url': '/dashboard/reviews',
            'action_text': 'View Reviews'
        }
        
        notification_ids = notification_service.schedule_notification(
            user_id=str(current_user.id),
            notification_type=NotificationType.REVIEW_REMINDER,
            delivery_channels=[DeliveryChannel.EMAIL, DeliveryChannel.IN_APP],
            content=test_content,
            priority=Priority.HIGH
        )
        
        logger.info(f"Sent test review reminder to user {current_user.id}: {notification_ids}")
    
    background_tasks.add_task(send_test)
    
    return {
        'message': 'Test review reminder sent',
        'user_id': str(current_user.id)
    }