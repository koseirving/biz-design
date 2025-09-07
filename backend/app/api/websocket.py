from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.websocket_service import websocket_manager, in_app_service
from app.core.security import verify_token
from pydantic import BaseModel
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()


class SystemAnnouncementRequest(BaseModel):
    message: str
    announcement_type: str = "info"  # info, warning, success, error
    target_user_ids: List[str] = None


class InAppNotificationRequest(BaseModel):
    user_id: str
    notification_type: str
    content: Dict[str, Any]
    persistent: bool = True


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time notifications"""
    
    try:
        # Verify token and get user
        payload = verify_token(token)
        if not payload or str(payload.get('sub')) != user_id:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        # Connect user
        await websocket_manager.connect(websocket, user_id)
        
        # Send any pending notifications
        await send_pending_notifications(db, user_id)
        
        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await handle_websocket_message(db, user_id, message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from user {user_id}: {data}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message from user {user_id}: {str(e)}")
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        finally:
            websocket_manager.disconnect(user_id)
            
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


async def handle_websocket_message(db: Session, user_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages from client"""
    
    message_type = message.get('type', 'unknown')
    
    if message_type == 'ping':
        # Respond to ping with pong
        await websocket_manager.send_personal_message(user_id, {
            'type': 'pong',
            'timestamp': message.get('timestamp')
        })
    
    elif message_type == 'mark_notification_read':
        # Mark notification as read
        notification_id = message.get('notification_id')
        if notification_id:
            in_app_service.mark_notification_read(db, notification_id, user_id)
    
    elif message_type == 'request_notifications':
        # Send pending notifications
        await send_pending_notifications(db, user_id)
    
    elif message_type == 'typing_start':
        # Handle typing indicators (for future chat features)
        await websocket_manager.send_typing_indicator(user_id, True)
    
    elif message_type == 'typing_stop':
        await websocket_manager.send_typing_indicator(user_id, False)
    
    else:
        logger.warning(f"Unknown WebSocket message type '{message_type}' from user {user_id}")


async def send_pending_notifications(db: Session, user_id: str):
    """Send any pending in-app notifications to the user"""
    
    try:
        # Get unread notifications
        notifications = in_app_service.get_unread_notifications(db, user_id)
        
        if notifications:
            # Send each notification
            for notification in notifications:
                await websocket_manager.send_personal_message(user_id, {
                    'type': 'notification',
                    'notification': notification
                })
            
            logger.info(f"Sent {len(notifications)} pending notifications to user {user_id}")
    
    except Exception as e:
        logger.error(f"Error sending pending notifications to user {user_id}: {str(e)}")


@router.get("/connections")
def get_active_connections(current_user: User = Depends(get_current_user)):
    """Get information about active WebSocket connections (admin only)"""
    
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    connections = websocket_manager.get_all_connections_info()
    
    return {
        'active_connections': connections,
        'total_connected': len(connections),
        'connection_summary': {
            'total_users': len(connections),
            'average_duration_minutes': sum(c['duration_minutes'] for c in connections) / len(connections) if connections else 0
        }
    }


@router.get("/my-connection")
def get_my_connection_info(current_user: User = Depends(get_current_user)):
    """Get current user's WebSocket connection information"""
    
    user_id = str(current_user.id)
    connection_info = websocket_manager.get_connection_info(user_id)
    
    if connection_info:
        return {
            'connected': True,
            'connection_info': connection_info
        }
    else:
        return {
            'connected': False,
            'message': 'No active WebSocket connection'
        }


@router.post("/send-notification")
async def send_in_app_notification(
    request: InAppNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send in-app notification to a specific user (admin only)"""
    
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        success = await in_app_service.send_notification(
            db=db,
            user_id=request.user_id,
            notification_type=request.notification_type,
            content=request.content,
            persistent=request.persistent
        )
        
        return {
            'success': success,
            'message': f'Notification sent to user {request.user_id}',
            'real_time_delivery': success
        }
        
    except Exception as e:
        logger.error(f"Failed to send in-app notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/broadcast-announcement")
async def broadcast_system_announcement(
    request: SystemAnnouncementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Broadcast system announcement to all connected users (admin only)"""
    
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await in_app_service.broadcast_system_announcement(
            db=db,
            message=request.message,
            announcement_type=request.announcement_type,
            target_user_ids=request.target_user_ids
        )
        
        return {
            'message': 'System announcement broadcast completed',
            'broadcast_result': result
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast announcement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast announcement: {str(e)}"
        )


@router.get("/notifications/unread")
def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, le=100)
):
    """Get unread in-app notifications for current user"""
    
    user_id = str(current_user.id)
    notifications = in_app_service.get_unread_notifications(db, user_id, limit)
    
    return {
        'user_id': user_id,
        'unread_notifications': notifications,
        'total_count': len(notifications),
        'has_websocket_connection': websocket_manager.is_user_connected(user_id)
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read"""
    
    user_id = str(current_user.id)
    
    try:
        in_app_service.mark_notification_read(db, notification_id, user_id)
        
        return {
            'message': f'Notification {notification_id} marked as read',
            'notification_id': notification_id
        }
        
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post("/test-websocket")
async def test_websocket_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test notification via WebSocket to current user"""
    
    user_id = str(current_user.id)
    
    try:
        # Send test notification
        await in_app_service.send_system_message(
            db=db,
            user_id=user_id,
            message="This is a test WebSocket notification! 🚀",
            message_type="success"
        )
        
        return {
            'message': 'Test notification sent',
            'user_id': user_id,
            'websocket_connected': websocket_manager.is_user_connected(user_id)
        }
        
    except Exception as e:
        logger.error(f"Failed to send test WebSocket notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )


@router.post("/cleanup-stale-connections")
async def cleanup_stale_connections(
    current_user: User = Depends(get_current_user),
    max_idle_minutes: int = Query(default=30, le=120),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Clean up stale WebSocket connections (admin only)"""
    
    if current_user.subscription_tier != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    async def cleanup():
        cleaned_count = await websocket_manager.cleanup_stale_connections(max_idle_minutes)
        logger.info(f"Cleaned up {cleaned_count} stale WebSocket connections")
    
    background_tasks.add_task(cleanup)
    
    return {
        'message': 'Stale connection cleanup initiated',
        'max_idle_minutes': max_idle_minutes
    }


@router.get("/stats")
def get_websocket_stats(current_user: User = Depends(get_current_user)):
    """Get WebSocket service statistics"""
    
    connected_users = websocket_manager.get_connected_users()
    connections_info = websocket_manager.get_all_connections_info()
    
    # Calculate statistics
    total_connected = len(connected_users)
    avg_duration = 0
    if connections_info:
        avg_duration = sum(c['duration_minutes'] for c in connections_info) / total_connected
    
    return {
        'websocket_stats': {
            'total_connected_users': total_connected,
            'average_connection_duration_minutes': round(avg_duration, 2),
            'user_connected': websocket_manager.is_user_connected(str(current_user.id)),
            'service_status': 'active'
        },
        'user_connection': websocket_manager.get_connection_info(str(current_user.id))
    }