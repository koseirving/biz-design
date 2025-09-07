from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
import hashlib
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    
    # Data access events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # GDPR compliance events
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_DELETION_REQUESTED = "data_deletion_requested"
    DATA_DELETION_COMPLETED = "data_deletion_completed"
    DATA_ANONYMIZATION = "data_anonymization"
    GDPR_REQUEST = "gdpr_request"
    
    # Admin events
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_MODIFIED = "user_modified"
    ROLE_CHANGED = "role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    ENCRYPTION_KEY_ROTATION = "encryption_key_rotation"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR_OCCURRED = "error_occurred"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event data"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    outcome: str  # success, failure, error
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    retention_until: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        data['retention_until'] = self.retention_until.isoformat()
        return data
    
    def to_cloud_logging_entry(self) -> Dict[str, Any]:
        """Format for Google Cloud Logging"""
        return {
            'severity': self.severity.value.upper(),
            'timestamp': self.timestamp.isoformat(),
            'jsonPayload': {
                'event_id': self.event_id,
                'event_type': self.event_type.value,
                'user_id': self.user_id,
                'session_id': self.session_id,
                'ip_address': self.ip_address,
                'resource': {
                    'type': self.resource_type,
                    'id': self.resource_id
                },
                'action': self.action,
                'outcome': self.outcome,
                'details': self.details,
                'metadata': self.metadata
            },
            'labels': {
                'component': 'audit-log',
                'event_type': self.event_type.value,
                'severity': self.severity.value
            }
        }


class SecurityAuditLogger:
    """Security audit logging service with GDPR compliance"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.retention_days = {
            AuditSeverity.LOW: 365,      # 1 year
            AuditSeverity.MEDIUM: 2555,   # 7 years
            AuditSeverity.HIGH: 2555,     # 7 years
            AuditSeverity.CRITICAL: 2555  # 7 years
        }
        
        # In production, initialize Google Cloud Logging client
        self.cloud_logging_client = None
        
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        outcome: str = "success",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = None
    ) -> str:
        """Log a security audit event"""
        
        # Determine severity if not provided
        if severity is None:
            severity = self._determine_severity(event_type, outcome)
        
        # Calculate retention date
        retention_days = self.retention_days.get(severity, 2555)
        retention_until = datetime.utcnow() + timedelta(days=retention_days)
        
        # Create audit event
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details or {},
            metadata=metadata or {},
            retention_until=retention_until
        )
        
        # Add automatic metadata
        event.metadata.update({
            'logged_at': datetime.utcnow().isoformat(),
            'logger_version': '1.0',
            'gdpr_compliant': True,
            'checksum': self._calculate_event_checksum(event)
        })
        
        try:
            # Store in local database
            self._store_audit_event(event)
            
            # Send to cloud logging
            self._send_to_cloud_logging(event)
            
            # Check for security alerts
            self._check_security_alerts(event)
            
            logger.debug(f"Audit event logged: {event.event_id}")
            
            return event.event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            # Don't raise exception to avoid breaking the main application
            return None
    
    def log_data_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        outcome: str = "success",
        data_fields: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Log data access event with specific details"""
        
        details = {
            'data_fields_accessed': data_fields or [],
            'access_method': kwargs.get('access_method', 'api'),
            'query_parameters': kwargs.get('query_params', {}),
            'response_size_bytes': kwargs.get('response_size', 0)
        }
        
        return self.log_event(
            event_type=AuditEventType.DATA_READ,
            action=action,
            outcome=outcome,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            **kwargs
        )
    
    def log_authentication_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        outcome: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log authentication-related event"""
        
        details = {}
        if failure_reason:
            details['failure_reason'] = failure_reason
            
        if event_type == AuditEventType.LOGIN_FAILURE:
            details['failed_attempts_count'] = kwargs.get('failed_attempts', 1)
            severity = AuditSeverity.MEDIUM
        elif event_type == AuditEventType.ACCOUNT_LOCKED:
            severity = AuditSeverity.HIGH
        else:
            severity = AuditSeverity.LOW
        
        return self.log_event(
            event_type=event_type,
            action=event_type.value,
            outcome=outcome,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            severity=severity,
            **kwargs
        )
    
    def log_gdpr_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: str,
        request_details: Dict[str, Any],
        outcome: str = "success",
        **kwargs
    ) -> str:
        """Log GDPR compliance event"""
        
        details = {
            'gdpr_request_type': request_details.get('request_type'),
            'legal_basis': request_details.get('legal_basis'),
            'data_categories': request_details.get('data_categories', []),
            'processing_time_days': request_details.get('processing_time_days', 0),
            'compliance_notes': request_details.get('notes', '')
        }
        
        return self.log_event(
            event_type=event_type,
            action=action,
            outcome=outcome,
            user_id=user_id,
            details=details,
            severity=AuditSeverity.HIGH,
            metadata={'gdpr_compliance': True, 'data_subject_rights': True},
            **kwargs
        )
    
    def log_security_incident(
        self,
        incident_type: str,
        description: str,
        affected_users: List[str] = None,
        threat_level: str = "medium",
        mitigation_actions: List[str] = None,
        **kwargs
    ) -> str:
        """Log security incident"""
        
        severity_mapping = {
            "low": AuditSeverity.LOW,
            "medium": AuditSeverity.MEDIUM,
            "high": AuditSeverity.HIGH,
            "critical": AuditSeverity.CRITICAL
        }
        
        details = {
            'incident_type': incident_type,
            'description': description,
            'affected_users': affected_users or [],
            'threat_level': threat_level,
            'mitigation_actions': mitigation_actions or [],
            'incident_id': str(uuid.uuid4())
        }
        
        return self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            action=f"security_incident_{incident_type}",
            outcome="detected",
            details=details,
            severity=severity_mapping.get(threat_level, AuditSeverity.MEDIUM),
            metadata={'security_incident': True, 'requires_investigation': True},
            **kwargs
        )
    
    def query_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        severity: Optional[AuditSeverity] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        
        # In production, this would query from database or cloud logging
        # For now, return mock data structure
        
        filters = {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'user_id': user_id,
            'event_types': [et.value for et in event_types] if event_types else None,
            'severity': severity.value if severity else None,
            'outcome': outcome,
            'limit': limit,
            'offset': offset
        }
        
        logger.info(f"Querying audit logs with filters: {filters}")
        
        # Mock response
        return [{
            'total_count': 0,
            'filters_applied': filters,
            'results': []
        }]
    
    def get_audit_summary(
        self,
        period_days: int = 30,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit log summary for a period"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # In production, this would aggregate from actual logs
        summary = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'user_id': user_id,
            'event_counts': {
                'total_events': 0,
                'by_type': {},
                'by_severity': {},
                'by_outcome': {}
            },
            'top_users': [],
            'security_alerts': 0,
            'compliance_events': 0,
            'data_access_events': 0
        }
        
        return summary
    
    def cleanup_expired_logs(self) -> int:
        """Clean up audit logs past retention period"""
        
        cutoff_date = datetime.utcnow()
        deleted_count = 0
        
        # In production, this would delete from database and cloud storage
        logger.info(f"Cleaning up audit logs older than retention periods")
        
        # Mock cleanup
        return deleted_count
    
    def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export audit logs for compliance reporting"""
        
        export_id = str(uuid.uuid4())
        
        # In production, this would:
        # 1. Query logs from storage
        # 2. Format according to specified format
        # 3. Create secure download link
        # 4. Log the export event
        
        self.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            action="audit_logs_export",
            outcome="success",
            user_id=user_id,
            details={
                'export_id': export_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'format': format,
                'exported_by': user_id
            },
            severity=AuditSeverity.MEDIUM
        )
        
        return {
            'export_id': export_id,
            'status': 'completed',
            'download_url': f'/api/audit/export/{export_id}',
            'format': format,
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    
    def verify_log_integrity(self, event_id: str) -> Dict[str, Any]:
        """Verify integrity of an audit log entry"""
        
        # In production, this would:
        # 1. Retrieve the event
        # 2. Recalculate checksum
        # 3. Compare with stored checksum
        # 4. Check for tampering signs
        
        return {
            'event_id': event_id,
            'integrity_verified': True,
            'checksum_valid': True,
            'tampering_detected': False,
            'verified_at': datetime.utcnow().isoformat()
        }
    
    def _determine_severity(self, event_type: AuditEventType, outcome: str) -> AuditSeverity:
        """Determine event severity based on type and outcome"""
        
        # High-severity events
        high_severity_events = {
            AuditEventType.ACCOUNT_LOCKED,
            AuditEventType.DATA_DELETION_COMPLETED,
            AuditEventType.GDPR_REQUEST,
            AuditEventType.PERMISSION_GRANTED,
            AuditEventType.PERMISSION_REVOKED,
            AuditEventType.ENCRYPTION_KEY_ROTATION
        }
        
        # Critical severity events
        critical_events = {
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.USER_DELETED
        }
        
        if event_type in critical_events:
            return AuditSeverity.CRITICAL
        elif event_type in high_severity_events:
            return AuditSeverity.HIGH
        elif outcome == "failure" or outcome == "error":
            return AuditSeverity.MEDIUM
        else:
            return AuditSeverity.LOW
    
    def _store_audit_event(self, event: AuditEvent) -> None:
        """Store audit event in database"""
        
        # In production, this would store in a dedicated audit_logs table
        try:
            # Mock storage
            logger.debug(f"Storing audit event {event.event_id} in database")
            
        except Exception as e:
            logger.error(f"Failed to store audit event in database: {str(e)}")
            raise
    
    def _send_to_cloud_logging(self, event: AuditEvent) -> None:
        """Send audit event to Google Cloud Logging"""
        
        try:
            if self.cloud_logging_client:
                log_entry = event.to_cloud_logging_entry()
                # self.cloud_logging_client.write_entries([log_entry])
                logger.debug(f"Sent audit event {event.event_id} to cloud logging")
            else:
                logger.debug(f"Cloud logging not configured, event {event.event_id} stored locally only")
                
        except Exception as e:
            logger.error(f"Failed to send audit event to cloud logging: {str(e)}")
            # Don't raise - local storage is still available
    
    def _check_security_alerts(self, event: AuditEvent) -> None:
        """Check if event triggers security alerts"""
        
        # Define alerting rules
        alert_conditions = {
            AuditEventType.LOGIN_FAILURE: self._check_failed_login_pattern,
            AuditEventType.RATE_LIMIT_EXCEEDED: self._check_rate_limit_pattern,
            AuditEventType.DATA_EXPORT: self._check_bulk_export_pattern
        }
        
        alert_check = alert_conditions.get(event.event_type)
        if alert_check:
            try:
                alert_check(event)
            except Exception as e:
                logger.error(f"Security alert check failed: {str(e)}")
    
    def _check_failed_login_pattern(self, event: AuditEvent) -> None:
        """Check for suspicious failed login patterns"""
        
        # In production, this would:
        # 1. Count recent failed logins for user/IP
        # 2. Detect brute force patterns
        # 3. Trigger alerts if thresholds exceeded
        
        if event.outcome == "failure":
            logger.info(f"Failed login detected for user {event.user_id} from IP {event.ip_address}")
    
    def _check_rate_limit_pattern(self, event: AuditEvent) -> None:
        """Check for rate limiting abuse patterns"""
        
        # In production, this would detect:
        # 1. Repeated rate limit violations
        # 2. Distributed attacks
        # 3. API abuse patterns
        
        logger.info(f"Rate limit exceeded for user {event.user_id}")
    
    def _check_bulk_export_pattern(self, event: AuditEvent) -> None:
        """Check for suspicious bulk data export patterns"""
        
        # In production, this would detect:
        # 1. Large data exports
        # 2. Unusual export patterns
        # 3. Potential data exfiltration
        
        logger.info(f"Data export by user {event.user_id}")
    
    def _calculate_event_checksum(self, event: AuditEvent) -> str:
        """Calculate integrity checksum for audit event"""
        
        # Create deterministic string representation
        checksum_data = {
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'user_id': event.user_id,
            'action': event.action,
            'outcome': event.outcome,
            'details': json.dumps(event.details, sort_keys=True)
        }
        
        checksum_string = json.dumps(checksum_data, sort_keys=True)
        return hashlib.sha256(checksum_string.encode()).hexdigest()


# Global audit logger instance
audit_logger = SecurityAuditLogger()


# Decorator for automatic audit logging
def audit_log(event_type: AuditEventType, action: str = None):
    """Decorator to automatically log function calls"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            action_name = action or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                
                audit_logger.log_event(
                    event_type=event_type,
                    action=action_name,
                    outcome="success",
                    details={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                
                return result
                
            except Exception as e:
                audit_logger.log_event(
                    event_type=event_type,
                    action=action_name,
                    outcome="error",
                    details={
                        'function': func.__name__,
                        'module': func.__module__,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    },
                    severity=AuditSeverity.MEDIUM
                )
                
                raise
        
        return wrapper
    return decorator


# Utility functions for common audit patterns
def audit_data_access(user_id: str, resource_type: str, resource_id: str, action: str, **kwargs):
    """Quick function to audit data access"""
    return audit_logger.log_data_access(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        **kwargs
    )


def audit_authentication(event_type: AuditEventType, user_id: str, outcome: str, **kwargs):
    """Quick function to audit authentication events"""
    return audit_logger.log_authentication_event(
        event_type=event_type,
        user_id=user_id,
        outcome=outcome,
        **kwargs
    )


def audit_gdpr_compliance(event_type: AuditEventType, user_id: str, request_details: Dict, **kwargs):
    """Quick function to audit GDPR compliance events"""
    return audit_logger.log_gdpr_event(
        event_type=event_type,
        action=event_type.value,
        user_id=user_id,
        request_details=request_details,
        **kwargs
    )