import json
import redis
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
from app.core.config import settings


class QueueType(str, Enum):
    EMAIL = "email_queue"
    PUSH = "push_queue"
    REMINDER = "reminder_queue"
    IN_APP = "in_app_queue"


class Priority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationQueueService:
    """Redis-based notification queue system with priority and delay support"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.NOTIFICATION_QUEUE_URL)
        
    def enqueue_notification(
        self,
        queue_type: QueueType,
        user_id: str,
        notification_data: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        delay_seconds: Optional[int] = None
    ) -> str:
        """Enqueue a notification with optional priority and delay"""
        
        notification_id = f"notification_{datetime.utcnow().timestamp()}_{user_id}"
        
        payload = {
            'id': notification_id,
            'user_id': user_id,
            'queue_type': queue_type.value,
            'priority': priority.value,
            'data': notification_data,
            'created_at': datetime.utcnow().isoformat(),
            'scheduled_at': (datetime.utcnow() + timedelta(seconds=delay_seconds)).isoformat() if delay_seconds else datetime.utcnow().isoformat(),
            'status': 'queued'
        }
        
        if delay_seconds:
            # For delayed notifications, use sorted set with timestamp as score
            delay_queue_key = f"delayed_{queue_type.value}"
            scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            self.redis_client.zadd(delay_queue_key, {json.dumps(payload): scheduled_time.timestamp()})
        else:
            # For immediate notifications, use priority queue
            queue_key = f"{queue_type.value}:priority_{priority.value}"
            self.redis_client.lpush(queue_key, json.dumps(payload))
        
        return notification_id
    
    def dequeue_notification(self, queue_type: QueueType) -> Optional[Dict[str, Any]]:
        """Dequeue highest priority notification from specified queue"""
        
        # Check priority queues from highest to lowest
        for priority in sorted(Priority, key=lambda x: x.value, reverse=True):
            queue_key = f"{queue_type.value}:priority_{priority.value}"
            notification_json = self.redis_client.rpop(queue_key)
            
            if notification_json:
                return json.loads(notification_json)
        
        return None
    
    def process_delayed_notifications(self, queue_type: QueueType) -> List[Dict[str, Any]]:
        """Move ready delayed notifications to immediate queue"""
        
        delay_queue_key = f"delayed_{queue_type.value}"
        current_time = datetime.utcnow().timestamp()
        
        # Get notifications that are ready to be sent
        ready_notifications = self.redis_client.zrangebyscore(
            delay_queue_key, 0, current_time, withscores=True
        )
        
        processed = []
        for notification_json, score in ready_notifications:
            notification_data = json.loads(notification_json)
            
            # Move to immediate queue with original priority
            priority = Priority(notification_data['priority'])
            queue_key = f"{queue_type.value}:priority_{priority.value}"
            self.redis_client.lpush(queue_key, notification_json)
            
            # Remove from delayed queue
            self.redis_client.zrem(delay_queue_key, notification_json)
            
            processed.append(notification_data)
        
        return processed
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about all notification queues"""
        
        stats = {
            'immediate_queues': {},
            'delayed_queues': {},
            'total_pending': 0
        }
        
        for queue_type in QueueType:
            # Immediate queue stats
            queue_stats = {}
            total_immediate = 0
            
            for priority in Priority:
                queue_key = f"{queue_type.value}:priority_{priority.value}"
                count = self.redis_client.llen(queue_key)
                queue_stats[f"priority_{priority.value}"] = count
                total_immediate += count
            
            stats['immediate_queues'][queue_type.value] = {
                'by_priority': queue_stats,
                'total': total_immediate
            }
            
            # Delayed queue stats
            delay_queue_key = f"delayed_{queue_type.value}"
            delayed_count = self.redis_client.zcard(delay_queue_key)
            stats['delayed_queues'][queue_type.value] = delayed_count
            
            stats['total_pending'] += total_immediate + delayed_count
        
        return stats
    
    def purge_queue(self, queue_type: QueueType, priority: Optional[Priority] = None) -> int:
        """Purge notifications from queue"""
        
        purged_count = 0
        
        if priority:
            # Purge specific priority queue
            queue_key = f"{queue_type.value}:priority_{priority.value}"
            purged_count = self.redis_client.delete(queue_key)
        else:
            # Purge all priority queues for this type
            for p in Priority:
                queue_key = f"{queue_type.value}:priority_{p.value}"
                purged_count += self.redis_client.delete(queue_key)
            
            # Also purge delayed queue
            delay_queue_key = f"delayed_{queue_type.value}"
            purged_count += self.redis_client.delete(delay_queue_key)
        
        return purged_count
    
    def peek_next_notification(self, queue_type: QueueType) -> Optional[Dict[str, Any]]:
        """Peek at next notification without removing it from queue"""
        
        for priority in sorted(Priority, key=lambda x: x.value, reverse=True):
            queue_key = f"{queue_type.value}:priority_{priority.value}"
            notification_json = self.redis_client.lindex(queue_key, -1)
            
            if notification_json:
                return json.loads(notification_json)
        
        return None
    
    def get_user_notifications(self, user_id: str, queue_type: Optional[QueueType] = None) -> List[Dict[str, Any]]:
        """Get all pending notifications for a specific user"""
        
        user_notifications = []
        queue_types_to_check = [queue_type] if queue_type else list(QueueType)
        
        for qt in queue_types_to_check:
            # Check immediate queues
            for priority in Priority:
                queue_key = f"{qt.value}:priority_{priority.value}"
                notifications = self.redis_client.lrange(queue_key, 0, -1)
                
                for notification_json in notifications:
                    notification = json.loads(notification_json)
                    if notification['user_id'] == user_id:
                        user_notifications.append(notification)
            
            # Check delayed queue
            delay_queue_key = f"delayed_{qt.value}"
            delayed_notifications = self.redis_client.zrange(delay_queue_key, 0, -1)
            
            for notification_json in delayed_notifications:
                notification = json.loads(notification_json)
                if notification['user_id'] == user_id:
                    user_notifications.append(notification)
        
        return user_notifications