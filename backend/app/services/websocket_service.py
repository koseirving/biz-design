from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.models.user import User, NotificationHistory
from app.core.deps import get_db
import json
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket connection manager for real-time notifications"""
    
    def __init__(self):
        # Store active connections: {user_id: {websocket, last_seen}}
        self.active_connections: Dict[str, Dict[str, any]] = {}
        # Store user sessions: {session_id: user_id}
        self.user_sessions: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str = None):
        """Connect a user's WebSocket"""
        await websocket.accept()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{datetime.utcnow().timestamp()}_{user_id}"
        
        # Store connection
        self.active_connections[user_id] = {
            'websocket': websocket,
            'session_id': session_id,
            'last_seen': datetime.utcnow(),
            'connected_at': datetime.utcnow()
        }
        
        self.user_sessions[session_id] = user_id
        
        logger.info(f"User {user_id} connected via WebSocket (session: {session_id})")
        
        # Send connection confirmation
        await self.send_personal_message(user_id, {
            'type': 'connection_confirmed',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Real-time notifications enabled'
        })
    
    def disconnect(self, user_id: str):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            session_id = self.active_connections[user_id]['session_id']
            
            # Clean up
            del self.active_connections[user_id]
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, user_id: str, message: Dict):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} not connected for personal message")
            return False
        
        try:
            connection = self.active_connections[user_id]
            websocket = connection['websocket']
            
            # Update last seen
            connection['last_seen'] = datetime.utcnow()
            
            # Send message
            await websocket.send_text(json.dumps(message))
            
            logger.debug(f"Sent personal message to user {user_id}: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
            # Remove stale connection
            self.disconnect(user_id)
            return False
    
    async def broadcast_message(self, message: Dict, user_ids: List[str] = None):
        """Broadcast message to all connected users or specific users"""
        target_users = user_ids if user_ids else list(self.active_connections.keys())
        
        successful_sends = 0
        failed_sends = 0
        
        for user_id in target_users:
            if user_id in self.active_connections:
                success = await self.send_personal_message(user_id, message)
                if success:
                    successful_sends += 1
                else:
                    failed_sends += 1
        
        logger.info(f"Broadcast completed: {successful_sends} successful, {failed_sends} failed")
        
        return {
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'total_targeted': len(target_users)
        }
    
    def get_connected_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user is currently connected"""
        return user_id in self.active_connections
    
    def get_connection_info(self, user_id: str) -> Dict:
        """Get connection information for a user"""
        if user_id not in self.active_connections:
            return None
        
        connection = self.active_connections[user_id]
        return {
            'user_id': user_id,
            'session_id': connection['session_id'],
            'connected_at': connection['connected_at'].isoformat(),
            'last_seen': connection['last_seen'].isoformat(),
            'duration_minutes': (datetime.utcnow() - connection['connected_at']).total_seconds() / 60
        }
    
    def get_all_connections_info(self) -> List[Dict]:
        """Get information about all active connections"""
        return [
            self.get_connection_info(user_id)
            for user_id in self.active_connections.keys()
        ]
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 30):
        """Clean up connections that haven't been seen recently"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_idle_minutes)
        stale_users = []
        
        for user_id, connection in self.active_connections.items():
            if connection['last_seen'] < cutoff_time:
                stale_users.append(user_id)
        
        for user_id in stale_users:
            logger.info(f"Cleaning up stale connection for user {user_id}")
            self.disconnect(user_id)
        
        return len(stale_users)
    
    async def send_typing_indicator(self, user_id: str, typing: bool = True):
        """Send typing indicator to user"""
        await self.send_personal_message(user_id, {
            'type': 'typing_indicator',
            'typing': typing,
            'timestamp': datetime.utcnow().isoformat()
        })


class InAppNotificationService:
    """Service for managing in-app notifications with WebSocket support"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def send_notification(
        self,
        db: Session,
        user_id: str,
        notification_type: str,
        content: Dict,
        persistent: bool = True
    ):
        """Send in-app notification to user"""
        
        # Create notification message
        notification_message = {
            'type': 'notification',
            'notification_type': notification_type,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'id': f"notif_{datetime.utcnow().timestamp()}_{user_id}",
            'persistent': persistent
        }
        
        # Store in database if persistent
        if persistent:
            self._store_notification(db, user_id, notification_message)
        
        # Send via WebSocket if user is connected
        if self.websocket_manager.is_user_connected(user_id):
            success = await self.websocket_manager.send_personal_message(
                user_id, notification_message
            )
            
            if success:
                logger.info(f"Real-time notification sent to user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send real-time notification to user {user_id}")
        
        logger.info(f"User {user_id} not connected, notification stored for later retrieval")
        return False
    
    async def send_achievement_notification(
        self,
        db: Session,
        user_id: str,
        achievement_data: Dict
    ):
        """Send achievement unlock notification"""
        
        content = {
            'title': f'🎉 Achievement Unlocked!',
            'message': f"You've earned: {achievement_data.get('badge_name', 'New Achievement')}",
            'achievement': achievement_data,
            'action_url': '/dashboard/badges',
            'priority': 'high',
            'show_celebration': True
        }
        
        await self.send_notification(
            db, user_id, 'achievement_unlock', content, persistent=True
        )
    
    async def send_review_reminder(
        self,
        db: Session,
        user_id: str,
        review_data: Dict
    ):
        """Send review reminder notification"""
        
        content = {
            'title': f'📚 Time to Review',
            'message': f"Your {review_data.get('framework_name', 'framework')} is ready for review",
            'review_data': review_data,
            'action_url': f"/reviews/outputs/{review_data.get('output_id')}",
            'priority': 'normal',
            'auto_dismiss_seconds': 30
        }
        
        await self.send_notification(
            db, user_id, 'review_reminder', content, persistent=True
        )
    
    async def send_system_message(
        self,
        db: Session,
        user_id: str,
        message: str,
        message_type: str = 'info'
    ):
        """Send system message to user"""
        
        content = {
            'title': 'System Message',
            'message': message,
            'message_type': message_type,  # info, warning, error, success
            'priority': 'low',
            'auto_dismiss_seconds': 10
        }
        
        await self.send_notification(
            db, user_id, 'system_message', content, persistent=False
        )
    
    async def send_progress_update(
        self,
        db: Session,
        user_id: str,
        progress_data: Dict
    ):
        """Send progress update notification"""
        
        content = {
            'title': f'🎯 Progress Update',
            'message': f"You've earned {progress_data.get('points_awarded', 0)} points!",
            'progress_data': progress_data,
            'priority': 'low',
            'show_animation': True,
            'auto_dismiss_seconds': 15
        }
        
        await self.send_notification(
            db, user_id, 'progress_update', content, persistent=False
        )
    
    def get_unread_notifications(self, db: Session, user_id: str, limit: int = 50) -> List[Dict]:
        """Get unread in-app notifications for user"""
        
        # Get from database
        notifications = db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.delivery_channel == 'in_app',
            NotificationHistory.status == 'sent'
        ).order_by(NotificationHistory.scheduled_at.desc()).limit(limit).all()
        
        return [
            {
                'id': str(notif.id),
                'type': notif.notification_type,
                'content': notif.content,
                'created_at': notif.scheduled_at.isoformat(),
                'read': False  # In a real system, track read status
            }
            for notif in notifications
        ]
    
    def mark_notification_read(self, db: Session, notification_id: str, user_id: str):
        """Mark notification as read"""
        
        # In a real system, you'd have a separate table for read status
        # For now, we'll just log it
        logger.info(f"Notification {notification_id} marked as read by user {user_id}")
    
    def _store_notification(self, db: Session, user_id: str, notification_message: Dict):
        """Store notification in database for persistence"""
        
        try:
            notification = NotificationHistory(
                user_id=user_id,
                notification_type=notification_message['notification_type'],
                delivery_channel='in_app',
                content=notification_message['content'],
                scheduled_at=datetime.utcnow(),
                sent_at=datetime.utcnow(),
                status='sent'
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store in-app notification: {str(e)}")
            db.rollback()
    
    async def broadcast_system_announcement(
        self,
        db: Session,
        message: str,
        announcement_type: str = 'info',
        target_user_ids: List[str] = None
    ):
        """Broadcast system announcement to all or specific users"""
        
        content = {
            'title': '📢 System Announcement',
            'message': message,
            'announcement_type': announcement_type,
            'priority': 'high',
            'dismissible': True
        }
        
        notification_message = {
            'type': 'system_announcement',
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'id': f"announce_{datetime.utcnow().timestamp()}"
        }
        
        # Broadcast via WebSocket
        result = await self.websocket_manager.broadcast_message(
            notification_message, target_user_ids
        )
        
        logger.info(f"System announcement broadcast: {result}")
        
        return result


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
in_app_service = InAppNotificationService(websocket_manager)