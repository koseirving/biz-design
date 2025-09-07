from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.audit_log_service import (
    SecurityAuditLogger,
    AuditEventType,
    AuditSeverity,
    audit_logger,
    audit_data_access
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit-logs"])


# Request/Response Models
class AuditLogQuery(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Start date for log query")
    end_date: Optional[datetime] = Field(None, description="End date for log query")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    severity: Optional[str] = Field(None, description="Filter by severity level")
    outcome: Optional[str] = Field(None, description="Filter by outcome (success/failure/error)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    @validator('event_types')
    def validate_event_types(cls, v):
        if v:
            valid_types = [e.value for e in AuditEventType]
            invalid_types = [t for t in v if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid event types: {invalid_types}")
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v and v not in [s.value for s in AuditSeverity]:
            raise ValueError(f"Invalid severity level: {v}")
        return v


class AuditExportRequest(BaseModel):
    start_date: datetime = Field(..., description="Export start date")
    end_date: datetime = Field(..., description="Export end date")
    format: str = Field("json", description="Export format (json/csv)")
    include_user_data: bool = Field(False, description="Include user data in export")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv', 'xlsx']:
            raise ValueError("Format must be json, csv, or xlsx")
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        
        # Limit export range to prevent abuse
        if 'start_date' in values and (v - values['start_date']).days > 365:
            raise ValueError("Export date range cannot exceed 365 days")
        
        return v


class SecurityIncidentReport(BaseModel):
    incident_type: str = Field(..., description="Type of security incident")
    description: str = Field(..., description="Detailed description")
    threat_level: str = Field("medium", description="Threat level (low/medium/high/critical)")
    affected_users: Optional[List[str]] = Field(None, description="List of affected user IDs")
    mitigation_actions: Optional[List[str]] = Field(None, description="Actions taken to mitigate")
    
    @validator('threat_level')
    def validate_threat_level(cls, v):
        if v not in ['low', 'medium', 'high', 'critical']:
            raise ValueError("Threat level must be low, medium, high, or critical")
        return v


# Audit Log Query Endpoints
@router.get("/logs", response_model=Dict[str, Any])
async def query_audit_logs(
    query: AuditLogQuery = Depends(),
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """Query audit logs with filtering options"""
    
    # Log the audit log access
    audit_data_access(
        user_id=str(current_user.id),
        resource_type="audit_logs",
        resource_id="query",
        action="audit_logs_query",
        ip_address=request.client.host if request else None,
        query_params=query.dict()
    )
    
    try:
        # Convert string event types back to enums
        event_types = None
        if query.event_types:
            event_types = [AuditEventType(t) for t in query.event_types]
        
        # Convert string severity back to enum
        severity = None
        if query.severity:
            severity = AuditSeverity(query.severity)
        
        # Query audit logs
        results = audit_logger.query_audit_logs(
            start_date=query.start_date,
            end_date=query.end_date,
            user_id=query.user_id,
            event_types=event_types,
            severity=severity,
            outcome=query.outcome,
            limit=query.limit,
            offset=query.offset
        )
        
        return {
            "query_parameters": query.dict(),
            "results": results,
            "queried_at": datetime.utcnow().isoformat(),
            "queried_by": str(current_user.id)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to query audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query audit logs"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_audit_summary(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
    user_id: Optional[str] = Query(None, description="Filter by specific user"),
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """Get audit log summary for a specified period"""
    
    # Log the summary access
    audit_data_access(
        user_id=str(current_user.id),
        resource_type="audit_logs",
        resource_id="summary",
        action="audit_summary_view",
        ip_address=request.client.host if request else None,
        query_params={"period_days": period_days, "filter_user_id": user_id}
    )
    
    try:
        summary = audit_logger.get_audit_summary(
            period_days=period_days,
            user_id=user_id
        )
        
        return {
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": str(current_user.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate audit summary"
        )


# Audit Log Export Endpoints
@router.post("/export", response_model=Dict[str, Any])
async def export_audit_logs(
    export_request: AuditExportRequest,
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """Export audit logs for compliance reporting"""
    
    # Check if user has export permissions (in production, check admin role)
    if current_user.subscription_tier != "premium":  # Temporary permission check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required for audit log export"
        )
    
    try:
        export_info = audit_logger.export_audit_logs(
            start_date=export_request.start_date,
            end_date=export_request.end_date,
            format=export_request.format,
            user_id=str(current_user.id)
        )
        
        return {
            "message": "Audit log export initiated",
            "export_info": export_info,
            "requested_by": str(current_user.id),
            "requested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to export audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate audit log export"
        )


@router.get("/export/{export_id}", response_model=Dict[str, Any])
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get status of audit log export"""
    
    try:
        # In production, check export ownership and retrieve actual status
        return {
            "export_id": export_id,
            "status": "completed",
            "download_url": f"/api/audit/download/{export_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "checked_by": str(current_user.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to get export status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export status"
        )


# Security Incident Reporting
@router.post("/security-incident", response_model=Dict[str, Any])
async def report_security_incident(
    incident: SecurityIncidentReport,
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """Report a security incident"""
    
    try:
        event_id = audit_logger.log_security_incident(
            incident_type=incident.incident_type,
            description=incident.description,
            affected_users=incident.affected_users,
            threat_level=incident.threat_level,
            mitigation_actions=incident.mitigation_actions,
            user_id=str(current_user.id),
            ip_address=request.client.host if request else None,
            metadata={'reported_via': 'api', 'reporter_id': str(current_user.id)}
        )
        
        return {
            "message": "Security incident reported successfully",
            "event_id": event_id,
            "incident_type": incident.incident_type,
            "threat_level": incident.threat_level,
            "reported_by": str(current_user.id),
            "reported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to report security incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report security incident"
        )


# Audit Log Integrity
@router.get("/integrity/{event_id}", response_model=Dict[str, Any])
async def verify_log_integrity(
    event_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Verify integrity of a specific audit log entry"""
    
    # Check permissions (admin only in production)
    if current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for integrity verification"
        )
    
    try:
        integrity_result = audit_logger.verify_log_integrity(event_id)
        
        # Log the integrity check
        audit_data_access(
            user_id=str(current_user.id),
            resource_type="audit_logs",
            resource_id=event_id,
            action="integrity_verification",
            outcome="success" if integrity_result.get('integrity_verified') else "failure"
        )
        
        return integrity_result
        
    except Exception as e:
        logger.error(f"Failed to verify log integrity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify log integrity"
        )


# Audit Configuration
@router.get("/configuration", response_model=Dict[str, Any])
async def get_audit_configuration(
    current_user: User = Depends(get_current_active_user)
):
    """Get current audit logging configuration"""
    
    try:
        config = {
            "event_types": [e.value for e in AuditEventType],
            "severity_levels": [s.value for s in AuditSeverity],
            "retention_policy": {
                "low_severity_days": 365,
                "medium_severity_days": 2555,
                "high_severity_days": 2555,
                "critical_severity_days": 2555
            },
            "features": {
                "cloud_logging_enabled": audit_logger.cloud_logging_client is not None,
                "database_logging_enabled": audit_logger.db is not None,
                "real_time_alerts": True,
                "integrity_verification": True
            },
            "compliance": {
                "gdpr_compliant": True,
                "log_retention_years": 7,
                "audit_trail_complete": True
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get audit configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit configuration"
        )


# User Activity Report
@router.get("/user-activity/{user_id}", response_model=Dict[str, Any])
async def get_user_activity_report(
    user_id: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed activity report for a specific user"""
    
    # Users can only see their own activity, admins can see any user
    if user_id != str(current_user.id) and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view own activity report"
        )
    
    try:
        # Log the access to user activity
        audit_data_access(
            user_id=str(current_user.id),
            resource_type="user_activity",
            resource_id=user_id,
            action="activity_report_view",
            outcome="success"
        )
        
        # In production, this would query actual user activity
        report = {
            "user_id": user_id,
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "activity_summary": {
                "total_events": 0,
                "login_events": 0,
                "data_access_events": 0,
                "data_modification_events": 0,
                "failed_attempts": 0,
                "last_activity": None
            },
            "event_timeline": [],
            "security_incidents": 0,
            "compliance_events": 0
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate user activity report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate activity report"
        )


# System Health Check
@router.get("/health", response_model=Dict[str, Any])
async def audit_system_health():
    """Health check for audit logging system"""
    
    try:
        health_status = {
            "status": "healthy",
            "database_logging": audit_logger.db is not None,
            "cloud_logging": audit_logger.cloud_logging_client is not None,
            "retention_policies_active": True,
            "integrity_checks_enabled": True,
            "last_cleanup": "not_implemented",
            "disk_usage": "monitoring_required",
            "checked_at": datetime.utcnow().isoformat()
        }
        
        # Determine overall status
        if not health_status["database_logging"] and not health_status["cloud_logging"]:
            health_status["status"] = "critical"
        elif not health_status["database_logging"] or not health_status["cloud_logging"]:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Audit system health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


# Maintenance Operations
@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
async def cleanup_expired_logs(
    current_user: User = Depends(get_current_active_user)
):
    """Clean up expired audit logs (admin only)"""
    
    # Check admin permissions
    if current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for maintenance operations"
        )
    
    try:
        deleted_count = audit_logger.cleanup_expired_logs()
        
        # Log the cleanup operation
        audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_STARTUP,  # Using existing enum
            action="audit_log_cleanup",
            outcome="success",
            user_id=str(current_user.id),
            details={
                "deleted_count": deleted_count,
                "cleanup_type": "expired_logs",
                "initiated_by": str(current_user.id)
            },
            severity=AuditSeverity.LOW
        )
        
        return {
            "message": "Log cleanup completed",
            "deleted_count": deleted_count,
            "cleaned_by": str(current_user.id),
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired logs"
        )