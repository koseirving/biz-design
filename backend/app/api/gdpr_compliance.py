from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.gdpr_compliance_service import (
    GDPRComplianceService, 
    ConsentType,
    is_eu_user,
    requires_gdpr_compliance,
    format_gdpr_notice
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr-compliance"])


# Request/Response Models
class ConsentUpdateRequest(BaseModel):
    consent_type: str = Field(..., description="Type of consent to update")
    granted: bool = Field(..., description="Whether consent is granted")
    reason: Optional[str] = Field("user_action", description="Reason for consent change")


class ConsentRecord(BaseModel):
    consents: Dict[str, bool] = Field(..., description="Consent preferences")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class DataSubjectRequest(BaseModel):
    request_type: str = Field(..., description="Type of GDPR request")
    additional_data: Optional[Dict[str, Any]] = Field({}, description="Additional request data")
    reason: Optional[str] = Field(None, description="Reason for the request")


# Consent Management Endpoints
@router.post("/consent/record", response_model=dict)
async def record_user_consent(
    consent_data: ConsentRecord,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record user's GDPR consent preferences"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        # Extract client information
        ip_address = consent_data.ip_address or request.client.host
        user_agent = consent_data.user_agent or request.headers.get("user-agent")
        
        consent_id = gdpr_service.consent_manager.record_consent(
            user_id=str(current_user.id),
            consent_data=consent_data.consents,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": "Consent recorded successfully",
            "consent_id": consent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "consents": consent_data.consents
        }
        
    except Exception as e:
        logger.error(f"Failed to record consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent"
        )


@router.get("/consent/current", response_model=dict)
async def get_current_consent(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's current consent preferences"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        consent_info = gdpr_service.consent_manager.get_user_consents(str(current_user.id))
        
        if not consent_info:
            # Return default consents for new users
            consent_info = {
                'user_id': str(current_user.id),
                'consents': {
                    ConsentType.ESSENTIAL: True,
                    ConsentType.ANALYTICS: False,
                    ConsentType.MARKETING: False,
                    ConsentType.PERSONALIZATION: False
                },
                'last_updated': None,
                'consent_string': None
            }
        
        return consent_info
        
    except Exception as e:
        logger.error(f"Failed to get consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consent information"
        )


@router.put("/consent/update", response_model=dict)
async def update_consent(
    consent_update: ConsentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update specific consent preference"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        # Validate consent type
        valid_types = [ConsentType.ESSENTIAL, ConsentType.ANALYTICS, ConsentType.MARKETING, ConsentType.PERSONALIZATION]
        if consent_update.consent_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid consent type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Essential consent cannot be withdrawn
        if consent_update.consent_type == ConsentType.ESSENTIAL and not consent_update.granted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Essential consent cannot be withdrawn as it's required for basic functionality"
            )
        
        success = gdpr_service.consent_manager.update_consent(
            user_id=str(current_user.id),
            consent_type=consent_update.consent_type,
            granted=consent_update.granted,
            reason=consent_update.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update consent"
            )
        
        return {
            "message": "Consent updated successfully",
            "consent_type": consent_update.consent_type,
            "granted": consent_update.granted,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update consent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consent"
        )


@router.delete("/consent/withdraw-all", status_code=status.HTTP_200_OK)
async def withdraw_all_consents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Withdraw all non-essential consents"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        success = gdpr_service.consent_manager.withdraw_all_consents(str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to withdraw consents"
            )
        
        return {
            "message": "All non-essential consents withdrawn successfully",
            "withdrawn_at": datetime.utcnow().isoformat(),
            "remaining_consents": {ConsentType.ESSENTIAL: True}
        }
        
    except Exception as e:
        logger.error(f"Failed to withdraw consents for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to withdraw consents"
        )


# Compliance Assessment Endpoints
@router.get("/compliance/assessment", response_model=dict)
async def get_compliance_assessment(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive GDPR compliance assessment for user"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        assessment = gdpr_service.assess_compliance(str(current_user.id))
        
        return assessment
        
    except Exception as e:
        logger.error(f"Failed to assess compliance for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance assessment"
        )


@router.get("/compliance/data-usage", response_model=dict)
async def get_data_usage_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analysis of user's data usage and retention"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        analysis = gdpr_service.data_minimization.analyze_data_usage(str(current_user.id))
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze data usage for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze data usage"
        )


# Data Subject Rights Endpoints
@router.post("/rights/exercise", response_model=dict)
async def exercise_data_subject_right(
    request_data: DataSubjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exercise GDPR data subject rights"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        # Validate request type
        valid_request_types = ['access', 'portability', 'rectification', 'erasure', 'restriction', 'objection']
        if request_data.request_type not in valid_request_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request type. Must be one of: {', '.join(valid_request_types)}"
            )
        
        response = gdpr_service.handle_data_subject_request(
            user_id=str(current_user.id),
            request_type=request_data.request_type,
            additional_data=request_data.additional_data
        )
        
        # Log the request for audit purposes
        logger.info(f"GDPR {request_data.request_type} request processed for user {current_user.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process GDPR request for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process {request_data.request_type} request"
        )


@router.get("/rights/status", response_model=dict)
async def get_user_rights_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of user's GDPR rights implementation"""
    
    try:
        gdpr_service = GDPRComplianceService(db)
        
        rights_status = gdpr_service._check_user_rights_compliance(str(current_user.id))
        
        return {
            "user_id": str(current_user.id),
            "rights_status": rights_status,
            "assessment_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rights status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user rights status"
        )


# Privacy Information Endpoints
@router.get("/privacy/notice/{notice_type}", response_model=dict)
async def get_privacy_notice(
    notice_type: str,
    request: Request
):
    """Get formatted privacy notice for different purposes"""
    
    try:
        # Check if user is likely from EU (for GDPR applicability)
        ip_address = request.client.host
        is_eu = is_eu_user(ip_address)
        
        notice = format_gdpr_notice(notice_type)
        
        return {
            "notice_type": notice_type,
            "title": notice['title'],
            "content": notice['content'],
            "gdpr_applicable": is_eu,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate privacy notice {notice_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate privacy notice"
        )


@router.get("/privacy/retention-policies", response_model=dict)
async def get_retention_policies():
    """Get data retention policies"""
    
    try:
        from app.services.gdpr_compliance_service import DataMinimizationService
        
        # Create a temporary service instance for policy information
        db = next(get_db())
        minimization_service = DataMinimizationService(db)
        
        policies = minimization_service.suggest_data_retention_policies()
        
        return {
            "retention_policies": policies,
            "policy_version": "1.0",
            "effective_date": "2024-01-01",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get retention policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve retention policies"
        )


# Note: GDPR middleware should be added to the main FastAPI app, not the router
# This functionality is handled in main.py middleware configuration


# Health check endpoint for GDPR compliance system
@router.get("/health", response_model=dict)
async def gdpr_compliance_health_check():
    """Health check for GDPR compliance system"""
    
    return {
        "status": "healthy",
        "gdpr_compliance_version": "1.0",
        "supported_rights": [
            "access", "portability", "rectification", 
            "erasure", "restriction", "objection"
        ],
        "consent_types": [
            ConsentType.ESSENTIAL, ConsentType.ANALYTICS,
            ConsentType.MARKETING, ConsentType.PERSONALIZATION
        ],
        "timestamp": datetime.utcnow().isoformat()
    }