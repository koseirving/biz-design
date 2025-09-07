from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, NotificationHistory, NotificationPreferences
from app.services.notification_queue_service import NotificationQueueService, QueueType, Priority
import logging

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    REVIEW_REMINDER = "review_reminder"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    BADGE_EARNED = "badge_earned"
    STREAK_MILESTONE = "streak_milestone"
    FRAMEWORK_COMPLETION = "framework_completion"
    WEEKLY_SUMMARY = "weekly_summary"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    WELCOME_SERIES = "welcome_series"


class DeliveryChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationProvider(ABC):
    """Abstract base class for notification providers"""
    
    @abstractmethod
    async def send_notification(self, user: User, content: Dict[str, Any]) -> bool:
        """Send notification to user"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider using SendGrid with template support"""
    
    def __init__(self, sendgrid_api_key: str):
        self.sendgrid_api_key = sendgrid_api_key
        from app.services.email_template_service import EmailTemplateService
        self.template_service = EmailTemplateService()
    
    async def send_notification(self, user: User, content: Dict[str, Any]) -> bool:
        """Send email notification with template support"""
        try:
            # Import here to avoid issues if sendgrid is not installed
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            import base64
            
            if not self.sendgrid_api_key:
                logger.error("SendGrid API key not configured")
                return False
            
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            # Use template if specified
            if 'template_name' in content and 'template_variables' in content:
                rendered_email = self.template_service.render_template(
                    template_name=content['template_name'],
                    user=user,
                    variables=content['template_variables'],
                    format_type='html'
                )
                
                html_content = rendered_email['content']
                subject = rendered_email['subject']
                
                # Also render text version
                text_rendered = self.template_service.render_template(
                    template_name=content['template_name'],
                    user=user,
                    variables=content['template_variables'],
                    format_type='text'
                )
                plain_text_content = text_rendered['content']
            else:
                # Use provided content
                html_content = content.get('html_content', '')
                plain_text_content = content.get('text_content', content.get('message', ''))
                subject = content.get('subject', 'Notification from Biz Design')
            
            # Create message
            message = Mail(
                from_email=content.get('from_email', 'noreply@bizdesign.ai'),
                to_emails=user.email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content
            )
            
            # Add custom headers
            message.custom_args = {
                'user_id': str(user.id),
                'notification_type': content.get('notification_type', 'unknown'),
                'environment': 'production'  # Could be configured
            }
            
            # Add tracking settings
            message.tracking_settings = {
                'click_tracking': {'enable': True, 'enable_text': False},
                'open_tracking': {'enable': True, 'substitution_tag': '%open-track%'},
                'subscription_tracking': {
                    'enable': True,
                    'text': 'Unsubscribe',
                    'html': '<a href="%unsubscribe_url%">Unsubscribe</a>'
                }
            }
            
            # Send email
            response = sg.send(message)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {user.email}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            return False
    
    def get_provider_name(self) -> str:
        return "sendgrid_email"
    
    async def send_test_email(self, user: User) -> bool:
        """Send a test email to verify configuration"""
        
        test_content = {
            'template_name': 'welcome_series',
            'template_variables': {
                'dashboard_url': 'https://bizdesign.ai/dashboard'
            }
        }
        
        return await self.send_notification(user, test_content)
    
    async def send_bulk_email(self, users: List[User], content: Dict[str, Any]) -> Dict[str, Any]:
        """Send bulk email to multiple users"""
        
        results = {
            'total_sent': 0,
            'total_failed': 0,
            'failed_emails': []
        }
        
        for user in users:
            try:
                success = await self.send_notification(user, content)
                if success:
                    results['total_sent'] += 1
                else:
                    results['total_failed'] += 1
                    results['failed_emails'].append(user.email)
            except Exception as e:
                logger.error(f"Bulk email failed for {user.email}: {str(e)}")
                results['total_failed'] += 1
                results['failed_emails'].append(user.email)
        
        return results


class PushNotificationProvider(NotificationProvider):
    """Push notification provider (placeholder for future implementation)"""
    
    async def send_notification(self, user: User, content: Dict[str, Any]) -> bool:
        """Send push notification"""
        # TODO: Implement push notification logic
        logger.info(f"Push notification would be sent to user {user.id}: {content.get('title', 'No title')}")
        return True
    
    def get_provider_name(self) -> str:
        return "push_provider"


class InAppNotificationProvider(NotificationProvider):
    """In-app notification provider"""
    
    async def send_notification(self, user: User, content: Dict[str, Any]) -> bool:
        """Store in-app notification in database/cache"""
        # For in-app notifications, we just need to store them
        # They will be retrieved by the frontend
        logger.info(f"In-app notification stored for user {user.id}: {content.get('title', 'No title')}")
        return True
    
    def get_provider_name(self) -> str:
        return "in_app_provider"


class NotificationService:
    """Main notification service with multi-provider support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.queue_service = NotificationQueueService()
        self.providers = {}
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup notification providers"""
        from app.core.config import settings
        
        # Email provider
        if settings.SENDGRID_API_KEY:
            self.providers[DeliveryChannel.EMAIL] = EmailNotificationProvider(settings.SENDGRID_API_KEY)
        
        # Push provider
        self.providers[DeliveryChannel.PUSH] = PushNotificationProvider()
        
        # In-app provider
        self.providers[DeliveryChannel.IN_APP] = InAppNotificationProvider()
    
    def schedule_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        delivery_channels: List[DeliveryChannel],
        content: Dict[str, Any],
        scheduled_at: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> List[str]:
        """Schedule notification for delivery"""
        
        notification_ids = []
        
        # Get user preferences
        user_prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        for channel in delivery_channels:
            # Check if user has enabled this channel
            if not self._is_channel_enabled(user_prefs, channel):
                continue
            
            # Prepare notification data
            notification_data = {
                'user_id': user_id,
                'notification_type': notification_type.value,
                'delivery_channel': channel.value,
                'content': content,
                'metadata': {
                    'provider': self.providers[channel].get_provider_name() if channel in self.providers else None,
                    'created_by_service': True
                }
            }
            
            # Calculate delay if scheduled for future
            delay_seconds = None
            if scheduled_at:
                delay_seconds = int((scheduled_at - datetime.utcnow()).total_seconds())
                if delay_seconds < 0:
                    delay_seconds = 0
            
            # Map channel to queue type
            queue_type = self._get_queue_type(channel)
            
            # Enqueue notification
            notification_id = self.queue_service.enqueue_notification(
                queue_type=queue_type,
                user_id=user_id,
                notification_data=notification_data,
                priority=priority,
                delay_seconds=delay_seconds
            )
            
            # Store in database
            self._store_notification_history(
                user_id=user_id,
                notification_type=notification_type,
                delivery_channel=channel,
                content=content,
                scheduled_at=scheduled_at or datetime.utcnow(),
                notification_id=notification_id
            )
            
            notification_ids.append(notification_id)
        
        return notification_ids
    
    async def process_notifications(self, queue_type: QueueType, batch_size: int = 10) -> int:
        """Process notifications from queue"""
        
        processed_count = 0
        
        # First, process any delayed notifications that are ready
        self.queue_service.process_delayed_notifications(queue_type)
        
        # Process immediate notifications
        for _ in range(batch_size):
            notification_data = self.queue_service.dequeue_notification(queue_type)
            if not notification_data:
                break
            
            try:
                success = await self._send_notification(notification_data)
                self._update_notification_status(
                    notification_data.get('id'),
                    NotificationStatus.SENT if success else NotificationStatus.FAILED
                )
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process notification {notification_data.get('id')}: {str(e)}")
                self._update_notification_status(
                    notification_data.get('id'),
                    NotificationStatus.FAILED
                )
        
        return processed_count
    
    async def _send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send notification using appropriate provider"""
        
        delivery_channel = DeliveryChannel(notification_data['data']['delivery_channel'])
        
        if delivery_channel not in self.providers:
            logger.error(f"No provider available for channel: {delivery_channel}")
            return False
        
        # Get user
        user = self.db.query(User).filter(User.id == notification_data['user_id']).first()
        if not user:
            logger.error(f"User not found: {notification_data['user_id']}")
            return False
        
        # Send notification
        provider = self.providers[delivery_channel]
        return await provider.send_notification(user, notification_data['data']['content'])
    
    def _is_channel_enabled(self, user_prefs: Optional[NotificationPreferences], channel: DeliveryChannel) -> bool:
        """Check if user has enabled specific notification channel"""
        
        if not user_prefs:
            return True  # Default to enabled if no preferences set
        
        if channel == DeliveryChannel.EMAIL:
            return user_prefs.email_enabled
        elif channel == DeliveryChannel.PUSH:
            return user_prefs.push_enabled
        elif channel == DeliveryChannel.IN_APP:
            return True  # In-app notifications are always enabled
        
        return False
    
    def _get_queue_type(self, channel: DeliveryChannel) -> QueueType:
        """Map delivery channel to queue type"""
        
        mapping = {
            DeliveryChannel.EMAIL: QueueType.EMAIL,
            DeliveryChannel.PUSH: QueueType.PUSH,
            DeliveryChannel.IN_APP: QueueType.IN_APP
        }
        
        return mapping.get(channel, QueueType.EMAIL)
    
    def _store_notification_history(
        self,
        user_id: str,
        notification_type: NotificationType,
        delivery_channel: DeliveryChannel,
        content: Dict[str, Any],
        scheduled_at: datetime,
        notification_id: str
    ):
        """Store notification in history table"""
        
        history_record = NotificationHistory(
            user_id=user_id,
            notification_type=notification_type.value,
            delivery_channel=delivery_channel.value,
            content=content,
            scheduled_at=scheduled_at,
            status=NotificationStatus.QUEUED.value
        )
        
        self.db.add(history_record)
        self.db.commit()
    
    def _update_notification_status(self, notification_id: str, status: NotificationStatus):
        """Update notification status in database"""
        
        # Extract user_id and timestamp from notification_id
        try:
            parts = notification_id.split('_')
            if len(parts) >= 3:
                timestamp = float(parts[1])
                user_id = parts[2]
                
                # Find and update the notification
                history_record = self.db.query(NotificationHistory).filter(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.status == NotificationStatus.QUEUED.value
                ).first()
                
                if history_record:
                    history_record.status = status.value
                    if status == NotificationStatus.SENT:
                        history_record.sent_at = datetime.utcnow()
                    self.db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to update notification status: {str(e)}")
    
    def get_user_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        
        total_sent = self.db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.status == NotificationStatus.SENT.value
        ).count()
        
        total_pending = len(self.queue_service.get_user_notifications(user_id))
        
        # Get recent notifications
        recent_notifications = self.db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id
        ).order_by(NotificationHistory.scheduled_at.desc()).limit(10).all()
        
        return {
            'total_sent': total_sent,
            'total_pending': total_pending,
            'recent_notifications': [
                {
                    'type': n.notification_type,
                    'channel': n.delivery_channel,
                    'scheduled_at': n.scheduled_at.isoformat(),
                    'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                    'status': n.status
                }
                for n in recent_notifications
            ]
        }
    
    def cancel_scheduled_notifications(
        self, 
        user_id: str, 
        notification_type: Optional[NotificationType] = None
    ) -> int:
        """Cancel scheduled notifications for a user"""
        
        # This is a simplified implementation
        # In a production system, you'd need more sophisticated queue management
        cancelled_count = 0
        
        # Update status in database
        query = self.db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.status.in_([NotificationStatus.PENDING.value, NotificationStatus.QUEUED.value])
        )
        
        if notification_type:
            query = query.filter(NotificationHistory.notification_type == notification_type.value)
        
        notifications = query.all()
        for notification in notifications:
            notification.status = NotificationStatus.CANCELLED.value
            cancelled_count += 1
        
        self.db.commit()
        
        return cancelled_count