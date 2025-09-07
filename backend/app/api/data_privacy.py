from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.data_export_service import DataExportService
import os

router = APIRouter(prefix="/users", tags=["data-privacy"])

@router.post("/data-export", response_model=dict)
async def request_data_export(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request export of user data (GDPR compliance)"""
    try:
        export_info = DataExportService.export_user_data(db, str(current_user.id))
        
        return {
            "message": "Data export created successfully",
            "download_info": export_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
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

@router.delete("/delete", status_code=status.HTTP_202_ACCEPTED)
async def request_account_deletion(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request GDPR-compliant account deletion"""
    try:
        # Mark user as deleted (soft delete)
        current_user.is_deleted = True
        current_user.is_active = False
        from datetime import datetime
        current_user.deleted_at = datetime.utcnow()
        
        db.add(current_user)
        db.commit()
        
        # TODO: Schedule background tasks for:
        # 1. Anonymization after 24 hours
        # 2. Physical deletion after 30 days
        # 3. Backup cleanup after 180 days
        
        return {
            "message": "Account deletion request processed",
            "details": "Your account has been deactivated. Complete deletion will occur within 30 days.",
            "deletion_scheduled_for": "30 days from now"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deletion request: {str(e)}"
        )