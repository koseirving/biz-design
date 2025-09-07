from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import (
    User, UserOutput, CompanyProfile, UserProgress,
    UserLearningSession, NotificationPreferences,
    NotificationHistory, UserBadge
)
from app.core.database import get_db
import logging
import json
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class DeletionStage(Enum):
    """Account deletion stages"""
    REQUESTED = "requested"           # User requested deletion
    SOFT_DELETED = "soft_deleted"     # Account deactivated
    ANONYMIZED = "anonymized"         # Personal data anonymized
    HARD_DELETED = "hard_deleted"     # All data physically deleted
    CANCELLED = "cancelled"           # Deletion request cancelled


class DeletionReason(Enum):
    """Reasons for account deletion"""
    USER_REQUEST = "user_request"
    GDPR_RIGHT = "gdpr_right"
    INACTIVITY = "inactivity"
    POLICY_VIOLATION = "policy_violation"
    DATA_RETENTION = "data_retention"


class AccountDeletionService:
    """GDPR-compliant account deletion service with staged deletion process"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Deletion timeline (in days)
        self.deletion_timeline = {
            DeletionStage.SOFT_DELETED: 0,    # Immediate
            DeletionStage.ANONYMIZED: 1,      # After 24 hours
            DeletionStage.HARD_DELETED: 30    # After 30 days
        }
    
    def initiate_deletion_request(
        self,
        user_id: str,
        reason: DeletionReason = DeletionReason.USER_REQUEST,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Initiate account deletion process"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.is_deleted:
            raise ValueError("User account already marked for deletion")
        
        deletion_id = str(uuid.uuid4())
        deletion_request = {
            'deletion_id': deletion_id,
            'user_id': user_id,
            'reason': reason.value,
            'stage': DeletionStage.REQUESTED.value,
            'requested_at': datetime.utcnow().isoformat(),
            'additional_data': additional_data or {},
            'timeline': self._calculate_deletion_timeline(),
            'cancellable_until': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        # Store deletion request (in production, use dedicated table)
        logger.info(f"Initiated deletion request {deletion_id} for user {user_id}")
        
        # Proceed to soft deletion immediately
        self._execute_soft_deletion(user, deletion_request)
        
        # Schedule subsequent stages (in production, use Cloud Tasks)
        self._schedule_deletion_stages(deletion_request)
        
        return deletion_request
    
    def _execute_soft_deletion(self, user: User, deletion_request: Dict[str, Any]) -> bool:
        """Execute soft deletion - deactivate account but keep data"""
        
        try:
            # Mark user as deleted
            user.is_deleted = True
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            
            # Add deletion metadata to user record
            user.deletion_metadata = {
                'deletion_id': deletion_request['deletion_id'],
                'stage': DeletionStage.SOFT_DELETED.value,
                'soft_deleted_at': datetime.utcnow().isoformat(),
                'reason': deletion_request['reason']
            }
            
            self.db.commit()
            
            deletion_request['stage'] = DeletionStage.SOFT_DELETED.value
            deletion_request['soft_deleted_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Soft deletion completed for user {user.id}")
            
            # Notify user of deletion (if they have email notifications enabled)
            self._send_deletion_notification(user, DeletionStage.SOFT_DELETED)
            
            return True
            
        except Exception as e:
            logger.error(f"Soft deletion failed for user {user.id}: {str(e)}")
            self.db.rollback()
            return False
    
    def _execute_anonymization(self, user_id: str, deletion_request: Dict[str, Any]) -> bool:
        """Execute anonymization - remove/anonymize personal data but keep analytical data"""
        
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for anonymization")
                return False
            
            # Anonymize user profile
            anonymized_email = f"deleted_user_{user_id[:8]}@anonymized.local"
            user.email = anonymized_email
            user.password_hash = "ANONYMIZED"
            
            # Update metadata
            if hasattr(user, 'deletion_metadata') and user.deletion_metadata:
                user.deletion_metadata['stage'] = DeletionStage.ANONYMIZED.value
                user.deletion_metadata['anonymized_at'] = datetime.utcnow().isoformat()
            
            # Anonymize related data while preserving analytical value
            self._anonymize_user_outputs(user_id)
            self._anonymize_learning_sessions(user_id)
            self._anonymize_notification_history(user_id)
            
            # Remove personal company profiles
            company_profiles = self.db.query(CompanyProfile).filter(
                CompanyProfile.user_id == user_id
            ).all()
            
            for profile in company_profiles:
                # Anonymize or delete depending on data sensitivity
                if self._contains_sensitive_data(profile.profile_data):
                    self.db.delete(profile)
                else:
                    profile.profile_name = f"Anonymized Profile {profile.id}"
                    profile.profile_data = self._anonymize_profile_data(profile.profile_data)
            
            self.db.commit()
            
            deletion_request['stage'] = DeletionStage.ANONYMIZED.value
            deletion_request['anonymized_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Anonymization completed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Anonymization failed for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def _execute_hard_deletion(self, user_id: str, deletion_request: Dict[str, Any]) -> bool:
        """Execute hard deletion - physically delete all user data"""
        
        try:
            # Delete all user-related records
            deletion_count = 0
            
            # Delete user outputs
            outputs = self.db.query(UserOutput).filter(UserOutput.user_id == user_id).all()
            for output in outputs:
                self.db.delete(output)
                deletion_count += 1
            
            # Delete company profiles
            profiles = self.db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).all()
            for profile in profiles:
                self.db.delete(profile)
                deletion_count += 1
            
            # Delete user progress
            progress_records = self.db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
            for progress in progress_records:
                self.db.delete(progress)
                deletion_count += 1
            
            # Delete learning sessions
            sessions = self.db.query(UserLearningSession).filter(UserLearningSession.user_id == user_id).all()
            for session in sessions:
                self.db.delete(session)
                deletion_count += 1
            
            # Delete notification preferences
            prefs = self.db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user_id).first()
            if prefs:
                self.db.delete(prefs)
                deletion_count += 1
            
            # Delete notification history (older than retention period only)
            retention_cutoff = datetime.utcnow() - timedelta(days=180)  # Keep for audit purposes
            old_notifications = self.db.query(NotificationHistory).filter(
                and_(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.created_at < retention_cutoff
                )
            ).all()
            
            for notification in old_notifications:
                self.db.delete(notification)
                deletion_count += 1
            
            # Delete user badges
            badges = self.db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
            for badge in badges:
                self.db.delete(badge)
                deletion_count += 1
            
            # Finally, delete the user record
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)
                deletion_count += 1
            
            self.db.commit()
            
            deletion_request['stage'] = DeletionStage.HARD_DELETED.value
            deletion_request['hard_deleted_at'] = datetime.utcnow().isoformat()
            deletion_request['records_deleted'] = deletion_count
            
            logger.info(f"Hard deletion completed for user {user_id}. Deleted {deletion_count} records.")
            
            # Log deletion for audit purposes
            self._log_deletion_completion(user_id, deletion_request)
            
            return True
            
        except Exception as e:
            logger.error(f"Hard deletion failed for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def cancel_deletion_request(self, user_id: str, deletion_id: str) -> bool:
        """Cancel pending deletion request (only if still in soft deletion stage)"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if deletion is cancellable
        if not hasattr(user, 'deletion_metadata') or not user.deletion_metadata:
            raise ValueError("No active deletion request found")
        
        deletion_metadata = user.deletion_metadata
        if deletion_metadata.get('deletion_id') != deletion_id:
            raise ValueError("Invalid deletion ID")
        
        current_stage = deletion_metadata.get('stage')
        if current_stage not in [DeletionStage.REQUESTED.value, DeletionStage.SOFT_DELETED.value]:
            raise ValueError("Deletion cannot be cancelled at this stage")
        
        # Check cancellation deadline
        cancellable_until = deletion_metadata.get('cancellable_until')
        if cancellable_until:
            cancellation_deadline = datetime.fromisoformat(cancellable_until.replace('Z', '+00:00'))
            if datetime.utcnow() > cancellation_deadline.replace(tzinfo=None):
                raise ValueError("Cancellation deadline has passed")
        
        try:
            # Restore user account
            user.is_deleted = False
            user.is_active = True
            user.deleted_at = None
            
            # Update deletion metadata
            deletion_metadata['stage'] = DeletionStage.CANCELLED.value
            deletion_metadata['cancelled_at'] = datetime.utcnow().isoformat()
            user.deletion_metadata = deletion_metadata
            
            self.db.commit()
            
            logger.info(f"Deletion request {deletion_id} cancelled for user {user_id}")
            
            # Notify user of cancellation
            self._send_deletion_notification(user, DeletionStage.CANCELLED)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel deletion for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_deletion_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current deletion status for user"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        if not user.is_deleted:
            return {
                'user_id': user_id,
                'status': 'active',
                'deletion_request': None
            }
        
        deletion_metadata = getattr(user, 'deletion_metadata', {})
        
        return {
            'user_id': user_id,
            'status': 'deletion_in_progress',
            'current_stage': deletion_metadata.get('stage'),
            'deletion_id': deletion_metadata.get('deletion_id'),
            'requested_at': deletion_metadata.get('requested_at'),
            'soft_deleted_at': deletion_metadata.get('soft_deleted_at'),
            'anonymized_at': deletion_metadata.get('anonymized_at'),
            'hard_deleted_at': deletion_metadata.get('hard_deleted_at'),
            'cancellable_until': deletion_metadata.get('cancellable_until'),
            'can_cancel': self._can_cancel_deletion(deletion_metadata)
        }
    
    def _calculate_deletion_timeline(self) -> Dict[str, str]:
        """Calculate deletion timeline with dates"""
        
        now = datetime.utcnow()
        timeline = {}
        
        for stage, days in self.deletion_timeline.items():
            timeline[stage.value] = (now + timedelta(days=days)).isoformat()
        
        return timeline
    
    def _schedule_deletion_stages(self, deletion_request: Dict[str, Any]) -> None:
        """Schedule deletion stages using Cloud Tasks (mock implementation)"""
        
        # In production, this would create Cloud Tasks
        deletion_id = deletion_request['deletion_id']
        user_id = deletion_request['user_id']
        
        # Schedule anonymization after 24 hours
        anonymization_time = datetime.utcnow() + timedelta(days=1)
        logger.info(f"Scheduled anonymization for {deletion_id} at {anonymization_time}")
        
        # Schedule hard deletion after 30 days
        hard_deletion_time = datetime.utcnow() + timedelta(days=30)
        logger.info(f"Scheduled hard deletion for {deletion_id} at {hard_deletion_time}")
        
        # In production:
        # - Create Cloud Task for anonymization
        # - Create Cloud Task for hard deletion
        # - Store task IDs in deletion_request
    
    def _anonymize_user_outputs(self, user_id: str) -> None:
        """Anonymize user outputs while preserving analytical value"""
        
        outputs = self.db.query(UserOutput).filter(UserOutput.user_id == user_id).all()
        
        for output in outputs:
            # Anonymize personal references in output data
            output_data = output.output_data.copy()
            
            # Remove or anonymize personal company names
            if 'company_name' in output_data:
                output_data['company_name'] = 'Anonymized Company'
            
            if 'personal_notes' in output_data:
                output_data['personal_notes'] = '[ANONYMIZED]'
            
            # Keep framework type and structure for analytics
            output.output_data = output_data
    
    def _anonymize_learning_sessions(self, user_id: str) -> None:
        """Anonymize learning sessions"""
        
        sessions = self.db.query(UserLearningSession).filter(
            UserLearningSession.user_id == user_id
        ).all()
        
        for session in sessions:
            if session.learning_data:
                learning_data = session.learning_data.copy()
                
                # Remove personal identifiers but keep learning metrics
                learning_data.pop('personal_notes', None)
                learning_data.pop('company_specific_examples', None)
                
                session.learning_data = learning_data
    
    def _anonymize_notification_history(self, user_id: str) -> None:
        """Anonymize notification history"""
        
        notifications = self.db.query(NotificationHistory).filter(
            NotificationHistory.user_id == user_id
        ).all()
        
        for notification in notifications:
            if notification.content:
                # Remove personal content but keep notification type for analytics
                anonymized_content = {
                    'type': notification.content.get('type', 'unknown'),
                    'timestamp': notification.content.get('timestamp'),
                    'anonymized': True
                }
                notification.content = anonymized_content
    
    def _contains_sensitive_data(self, profile_data: Dict[str, Any]) -> bool:
        """Check if profile data contains sensitive personal information"""
        
        sensitive_fields = [
            'email', 'phone', 'address', 'ssn', 'tax_id',
            'personal_contacts', 'financial_data'
        ]
        
        return any(field in profile_data for field in sensitive_fields)
    
    def _anonymize_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize profile data"""
        
        anonymized_data = profile_data.copy()
        
        # Replace sensitive fields
        if 'company_name' in anonymized_data:
            anonymized_data['company_name'] = 'Anonymized Company'
        
        if 'description' in anonymized_data:
            anonymized_data['description'] = '[ANONYMIZED]'
        
        # Remove personal fields
        personal_fields = ['contact_info', 'owner_details', 'financial_info']
        for field in personal_fields:
            anonymized_data.pop(field, None)
        
        anonymized_data['anonymized'] = True
        anonymized_data['anonymized_at'] = datetime.utcnow().isoformat()
        
        return anonymized_data
    
    def _can_cancel_deletion(self, deletion_metadata: Dict[str, Any]) -> bool:
        """Check if deletion can still be cancelled"""
        
        current_stage = deletion_metadata.get('stage')
        if current_stage not in [DeletionStage.REQUESTED.value, DeletionStage.SOFT_DELETED.value]:
            return False
        
        cancellable_until = deletion_metadata.get('cancellable_until')
        if not cancellable_until:
            return False
        
        deadline = datetime.fromisoformat(cancellable_until.replace('Z', '+00:00'))
        return datetime.utcnow() < deadline.replace(tzinfo=None)
    
    def _send_deletion_notification(self, user: User, stage: DeletionStage) -> None:
        """Send notification about deletion status (mock implementation)"""
        
        notifications = {
            DeletionStage.SOFT_DELETED: {
                'subject': 'Account Deletion Request Received',
                'message': 'Your account deletion request has been received and processed. Your account has been deactivated.'
            },
            DeletionStage.ANONYMIZED: {
                'subject': 'Account Data Anonymized',
                'message': 'Your personal data has been anonymized as part of the deletion process.'
            },
            DeletionStage.HARD_DELETED: {
                'subject': 'Account Deletion Completed',
                'message': 'Your account and all associated data have been permanently deleted.'
            },
            DeletionStage.CANCELLED: {
                'subject': 'Account Deletion Cancelled',
                'message': 'Your account deletion request has been cancelled and your account has been reactivated.'
            }
        }
        
        notification_info = notifications.get(stage)
        if notification_info:
            logger.info(f"Sending {stage.value} notification to user {user.id}")
            # In production, send actual notification via NotificationService
    
    def _log_deletion_completion(self, user_id: str, deletion_request: Dict[str, Any]) -> None:
        """Log deletion completion for audit purposes"""
        
        audit_log = {
            'event_type': 'account_hard_deletion_completed',
            'user_id': user_id,
            'deletion_id': deletion_request['deletion_id'],
            'completed_at': datetime.utcnow().isoformat(),
            'records_deleted': deletion_request.get('records_deleted', 0),
            'reason': deletion_request.get('reason'),
            'gdpr_compliance': True
        }
        
        logger.info(f"AUDIT: {json.dumps(audit_log)}")
    
    def cleanup_old_deletion_requests(self) -> int:
        """Clean up old deletion request metadata"""
        
        # This would clean up completed deletion requests older than retention period
        # For now, just log the action
        logger.info("Cleanup of old deletion requests would be performed here")
        return 0


# Utility functions for deletion service

def validate_deletion_request(user: User, reason: DeletionReason) -> List[str]:
    """Validate if user account can be deleted"""
    
    errors = []
    
    if user.is_deleted:
        errors.append("Account is already marked for deletion")
    
    if not user.is_active:
        errors.append("Account is already inactive")
    
    # Add business rule validations
    if reason == DeletionReason.INACTIVITY:
        # Check if user has been inactive long enough
        if user.created_at and (datetime.utcnow() - user.created_at).days < 365:
            errors.append("Account is not old enough for inactivity deletion")
    
    return errors


def estimate_deletion_impact(db: Session, user_id: str) -> Dict[str, int]:
    """Estimate the impact of deleting a user account"""
    
    impact = {
        'outputs': db.query(UserOutput).filter(UserOutput.user_id == user_id).count(),
        'company_profiles': db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).count(),
        'progress_records': db.query(UserProgress).filter(UserProgress.user_id == user_id).count(),
        'learning_sessions': db.query(UserLearningSession).filter(UserLearningSession.user_id == user_id).count(),
        'badges': db.query(UserBadge).filter(UserBadge.user_id == user_id).count(),
        'notifications': db.query(NotificationHistory).filter(NotificationHistory.user_id == user_id).count()
    }
    
    impact['total_records'] = sum(impact.values())
    
    return impact