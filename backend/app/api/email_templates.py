from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.email_template_service import EmailTemplateService
from app.services.notification_service import NotificationService
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class EmailPreviewRequest(BaseModel):
    template_name: str
    sample_variables: Optional[Dict[str, Any]] = None


class TestEmailRequest(BaseModel):
    template_name: str
    template_variables: Dict[str, Any]


class BulkEmailRequest(BaseModel):
    template_name: str
    template_variables: Dict[str, Any]
    user_filters: Optional[Dict[str, Any]] = None
    test_mode: bool = True


@router.get("/templates")
def get_available_templates():
    """Get list of available email templates"""
    
    template_service = EmailTemplateService()
    templates = template_service.get_available_templates()
    
    return {
        'templates': templates,
        'total_count': len(templates)
    }


@router.post("/templates/{template_name}/preview")
def preview_email_template(
    template_name: str,
    request: EmailPreviewRequest = EmailPreviewRequest(template_name=""),
    current_user: User = Depends(get_current_user)
):
    """Preview an email template with sample data"""
    
    template_service = EmailTemplateService()
    
    try:
        preview = template_service.preview_template(
            template_name=template_name,
            sample_variables=request.sample_variables
        )
        
        return {
            'preview': preview,
            'template_name': template_name
        }
        
    except Exception as e:
        logger.error(f"Failed to preview template {template_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to preview template: {str(e)}"
        )


@router.post("/test-send")
async def send_test_email(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Send a test email using specified template"""
    
    async def send_test():
        try:
            notification_service = NotificationService(db)
            
            # Check if email provider is available
            from app.services.notification_service import DeliveryChannel
            if DeliveryChannel.EMAIL not in notification_service.providers:
                logger.error("Email provider not configured")
                return
            
            email_provider = notification_service.providers[DeliveryChannel.EMAIL]
            
            # Prepare test content
            test_content = {
                'template_name': request.template_name,
                'template_variables': request.template_variables,
                'notification_type': 'test_email'
            }
            
            # Send test email
            success = await email_provider.send_notification(current_user, test_content)
            
            if success:
                logger.info(f"Test email sent to {current_user.email} using template {request.template_name}")
            else:
                logger.error(f"Failed to send test email to {current_user.email}")
                
        except Exception as e:
            logger.error(f"Test email error: {str(e)}")
    
    background_tasks.add_task(send_test)
    
    return {
        'message': f'Test email scheduled for delivery',
        'recipient': current_user.email,
        'template_name': request.template_name
    }


@router.post("/bulk-send")
async def send_bulk_email(
    request: BulkEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Send bulk email to users (admin only)"""
    
    # TODO: Add admin authorization check
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for bulk email operations"
        )
    
    async def send_bulk():
        try:
            notification_service = NotificationService(db)
            
            # Get target users based on filters
            users_query = db.query(User)
            
            if request.user_filters:
                # Apply filters
                if 'subscription_tier' in request.user_filters:
                    users_query = users_query.filter(
                        User.subscription_tier == request.user_filters['subscription_tier']
                    )
                
                if 'active_only' in request.user_filters and request.user_filters['active_only']:
                    users_query = users_query.filter(User.is_active == True)
            
            target_users = users_query.limit(100).all()  # Limit for safety
            
            if request.test_mode:
                # In test mode, only send to current user
                target_users = [current_user]
            
            # Check if email provider is available
            from app.services.notification_service import DeliveryChannel
            if DeliveryChannel.EMAIL not in notification_service.providers:
                logger.error("Email provider not configured")
                return
            
            email_provider = notification_service.providers[DeliveryChannel.EMAIL]
            
            # Prepare bulk content
            bulk_content = {
                'template_name': request.template_name,
                'template_variables': request.template_variables,
                'notification_type': 'bulk_email'
            }
            
            # Send bulk emails
            results = await email_provider.send_bulk_email(target_users, bulk_content)
            
            logger.info(f"Bulk email completed: {results['total_sent']} sent, {results['total_failed']} failed")
            
        except Exception as e:
            logger.error(f"Bulk email error: {str(e)}")
    
    background_tasks.add_task(send_bulk)
    
    return {
        'message': 'Bulk email job scheduled',
        'template_name': request.template_name,
        'test_mode': request.test_mode,
        'estimated_recipients': 1 if request.test_mode else 'filtered_count'
    }


@router.get("/delivery-stats")
def get_email_delivery_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get email delivery statistics"""
    
    from app.models.user import NotificationHistory
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Get email delivery stats from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    email_stats = db.query(
        NotificationHistory.status,
        func.count(NotificationHistory.id).label('count')
    ).filter(
        and_(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.delivery_channel == 'email',
            NotificationHistory.scheduled_at >= thirty_days_ago
        )
    ).group_by(NotificationHistory.status).all()
    
    stats = {status: count for status, count in email_stats}
    
    # Get recent email activity
    recent_emails = db.query(NotificationHistory).filter(
        and_(
            NotificationHistory.user_id == current_user.id,
            NotificationHistory.delivery_channel == 'email'
        )
    ).order_by(NotificationHistory.scheduled_at.desc()).limit(10).all()
    
    return {
        'user_id': str(current_user.id),
        'period_days': 30,
        'delivery_stats': stats,
        'recent_activity': [
            {
                'notification_type': email.notification_type,
                'status': email.status,
                'scheduled_at': email.scheduled_at.isoformat(),
                'sent_at': email.sent_at.isoformat() if email.sent_at else None
            }
            for email in recent_emails
        ]
    }


@router.post("/test-sendgrid-config")
async def test_sendgrid_configuration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test SendGrid configuration with a simple email"""
    
    try:
        notification_service = NotificationService(db)
        
        # Check if email provider is available
        from app.services.notification_service import DeliveryChannel
        if DeliveryChannel.EMAIL not in notification_service.providers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service not configured"
            )
        
        email_provider = notification_service.providers[DeliveryChannel.EMAIL]
        
        # Send test email
        success = await email_provider.send_test_email(current_user)
        
        if success:
            return {
                'status': 'success',
                'message': 'Test email sent successfully',
                'recipient': current_user.email
            }
        else:
            return {
                'status': 'failed',
                'message': 'Test email failed to send',
                'recipient': current_user.email
            }
            
    except Exception as e:
        logger.error(f"SendGrid test error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SendGrid test failed: {str(e)}"
        )


@router.get("/unsubscribe")
def handle_unsubscribe(token: str, db: Session = Depends(get_db)):
    """Handle email unsubscribe requests"""
    
    # TODO: Implement proper token validation and unsubscribe logic
    # This is a simplified version
    
    try:
        # In production, validate token and get user
        # For now, return a success message
        
        return {
            'message': 'Successfully unsubscribed from email notifications',
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Unsubscribe error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid unsubscribe token"
        )


@router.post("/schedule-review-reminders")
async def schedule_review_reminders_bulk(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Schedule review reminders for all user outputs (admin function)"""
    
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    async def schedule_bulk_reminders():
        try:
            from app.services.review_scheduler_service import ReviewSchedulerService
            from app.models.user import UserOutput
            
            scheduler_service = ReviewSchedulerService(db)
            
            # Get all user outputs
            all_outputs = db.query(UserOutput).all()
            
            scheduled_count = 0
            for output in all_outputs:
                user = db.query(User).filter(User.id == output.user_id).first()
                if user:
                    notification_ids = scheduler_service.schedule_reviews_for_output(user, output)
                    if notification_ids:
                        scheduled_count += len(notification_ids)
            
            logger.info(f"Bulk scheduled {scheduled_count} review reminders")
            
        except Exception as e:
            logger.error(f"Bulk scheduling error: {str(e)}")
    
    background_tasks.add_task(schedule_bulk_reminders)
    
    return {
        'message': 'Bulk review reminder scheduling initiated',
        'status': 'scheduled'
    }