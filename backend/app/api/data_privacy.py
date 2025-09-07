from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.data_export_service import DataExportService, ExportFormat
from app.services.account_deletion_service import (
    AccountDeletionService, 
    DeletionReason,
    validate_deletion_request,
    estimate_deletion_impact
)
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["data-privacy"])


# Request models
class DataExportRequest(BaseModel):
    formats: List[str] = Field(default=[ExportFormat.JSON, ExportFormat.CSV], description="Export formats")


class AccountDeletionRequest(BaseModel):
    reason: str = Field(default=DeletionReason.USER_REQUEST.value, description="Reason for deletion")
    confirm_deletion: bool = Field(..., description="Confirmation that user wants to delete account")
    understand_consequences: bool = Field(..., description="User understands deletion consequences")

@router.post("/data-export", response_model=dict)
async def request_data_export(
    export_request: DataExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request export of user data (GDPR compliance) with multiple format support"""
    try:
        # Validate export formats
        valid_formats = [ExportFormat.JSON, ExportFormat.CSV, ExportFormat.XML, ExportFormat.PDF]
        invalid_formats = [fmt for fmt in export_request.formats if fmt not in valid_formats]
        
        if invalid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export formats: {', '.join(invalid_formats)}"
            )
        
        # Create export service instance
        export_service = DataExportService()
        
        # Create export request
        export_info = export_service.create_export_request(
            db=db,
            user_id=str(current_user.id),
            formats=export_request.formats
        )
        
        logger.info(f"Data export requested by user {current_user.id}")
        
        return {
            "message": "Data export created successfully",
            "export_info": export_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data export failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


@router.get("/export-status/{export_id}", response_model=dict)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a data export request"""
    try:
        export_service = DataExportService()
        status_info = export_service.get_export_status(export_id)
        
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get export status {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export status"
        )

@router.get("/download/{filename}")
async def download_export_file(filename: str):
    """Download exported data file"""
    file_path = f"/tmp/exports/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found or expired"
        )
    
    # Determine media type based on file extension
    media_type = "application/json" if filename.endswith('.json') else "text/csv"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@router.get("/deletion-impact", response_model=dict)
async def get_deletion_impact(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get impact assessment of account deletion"""
    try:
        impact = estimate_deletion_impact(db, str(current_user.id))
        
        return {
            "user_id": str(current_user.id),
            "impact_assessment": impact,
            "warning": "Deletion will permanently remove all data listed above",
            "cancellation_period": "30 days"
        }
        
    except Exception as e:
        logger.error(f"Failed to assess deletion impact for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess deletion impact"
        )


@router.post("/request-deletion", status_code=status.HTTP_202_ACCEPTED)
async def request_account_deletion(
    deletion_request: AccountDeletionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request GDPR-compliant staged account deletion"""
    try:
        # Validate request
        if not deletion_request.confirm_deletion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account deletion must be confirmed"
            )
        
        if not deletion_request.understand_consequences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must understand deletion consequences"
            )
        
        # Validate deletion reason
        try:
            reason = DeletionReason(deletion_request.reason)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid deletion reason"
            )
        
        # Validate if user can be deleted
        validation_errors = validate_deletion_request(current_user, reason)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete account: {'; '.join(validation_errors)}"
            )
        
        # Create deletion service and initiate deletion
        deletion_service = AccountDeletionService(db)
        
        deletion_info = deletion_service.initiate_deletion_request(
            user_id=str(current_user.id),
            reason=reason,
            additional_data={
                'requested_via': 'api',
                'ip_address': 'unknown',  # Would get from request in production
                'user_agent': 'unknown'
            }
        )
        
        logger.info(f"Account deletion requested by user {current_user.id}")
        
        return {
            "message": "Account deletion request processed successfully",
            "deletion_info": deletion_info,
            "next_steps": {
                "immediate": "Account deactivated",
                "24_hours": "Personal data anonymized",
                "30_days": "All data permanently deleted"
            },
            "cancellation": {
                "possible_until": deletion_info.get('cancellable_until'),
                "instructions": "Contact support or use cancellation endpoint"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion request failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deletion request: {str(e)}"
        )


@router.post("/cancel-deletion/{deletion_id}", response_model=dict)
async def cancel_account_deletion(
    deletion_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel pending account deletion request"""
    try:
        deletion_service = AccountDeletionService(db)
        
        success = deletion_service.cancel_deletion_request(
            user_id=str(current_user.id),
            deletion_id=deletion_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel deletion request"
            )
        
        logger.info(f"Account deletion cancelled by user {current_user.id}")
        
        return {
            "message": "Account deletion request cancelled successfully",
            "deletion_id": deletion_id,
            "account_status": "reactivated",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion cancellation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel deletion: {str(e)}"
        )


@router.get("/deletion-status", response_model=dict)
async def get_deletion_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current deletion status for user account"""
    try:
        deletion_service = AccountDeletionService(db)
        
        status_info = deletion_service.get_deletion_status(str(current_user.id))
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deletion status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deletion status"
        )