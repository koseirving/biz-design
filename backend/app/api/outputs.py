from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.output_service import OutputService, OutputVersionService
from app.services.framework_service import FrameworkService
from datetime import datetime

router = APIRouter()


# Schemas for outputs
class OutputBase(BaseModel):
    framework_id: str
    output_data: Dict[str, Any]


class OutputCreate(OutputBase):
    pass


class OutputUpdate(BaseModel):
    output_data: Dict[str, Any]


class OutputResponse(BaseModel):
    id: str
    user_id: str
    framework_id: str
    output_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VersionResponse(BaseModel):
    id: str
    output_id: str
    version_number: int
    version_data: Dict[str, Any]
    created_at: datetime
    is_current: bool
    
    class Config:
        from_attributes = True


# Output CRUD endpoints
@router.get("/", response_model=List[OutputResponse])
async def get_user_outputs(
    framework_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's outputs"""
    outputs = OutputService.get_user_outputs(
        db=db,
        user_id=str(current_user.id),
        framework_id=framework_id,
        skip=skip,
        limit=limit
    )
    
    return [OutputResponse.from_orm(output) for output in outputs]


@router.post("/", response_model=OutputResponse)
async def create_output(
    output: OutputCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new output"""
    # Verify framework exists and user has access
    framework = FrameworkService.get_framework_by_id(db, output.framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    # Check premium access
    if framework.is_premium and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required to use this framework"
        )
    
    db_output = OutputService.create_output(
        db=db,
        user_id=str(current_user.id),
        framework_id=output.framework_id,
        output_data=output.output_data
    )
    
    return OutputResponse.from_orm(db_output)


@router.get("/{output_id}", response_model=OutputResponse)
async def get_output(
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific output"""
    output = OutputService.get_output_by_id(db, output_id, str(current_user.id))
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    return OutputResponse.from_orm(output)


@router.put("/{output_id}", response_model=OutputResponse)
async def update_output(
    output_id: str,
    output_update: OutputUpdate,
    create_version: bool = Query(False, description="Whether to create a new version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an output"""
    db_output = OutputService.update_output(
        db=db,
        output_id=output_id,
        user_id=str(current_user.id),
        output_data=output_update.output_data,
        create_version=create_version
    )
    
    if not db_output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    return OutputResponse.from_orm(db_output)


@router.delete("/{output_id}")
async def delete_output(
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an output"""
    success = OutputService.delete_output(db, output_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Output not found")
    
    return {"message": "Output deleted successfully"}


@router.post("/{output_id}/auto-save", response_model=OutputResponse)
async def auto_save_output(
    output_id: str,
    output_update: OutputUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-save output (for draft functionality)"""
    db_output = OutputService.auto_save_output(
        db=db,
        output_id=output_id,
        user_id=str(current_user.id),
        output_data=output_update.output_data
    )
    
    if not db_output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    return OutputResponse.from_orm(db_output)


# Version management endpoints
@router.get("/{output_id}/versions", response_model=List[VersionResponse])
async def get_output_versions(
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions of an output"""
    # Verify user owns the output
    output = OutputService.get_output_by_id(db, output_id, str(current_user.id))
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    versions = OutputVersionService.get_versions(db, output_id)
    return [VersionResponse.from_orm(version) for version in versions]


@router.post("/{output_id}/versions", response_model=VersionResponse)
async def create_output_version(
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new version of an output"""
    output = OutputService.get_output_by_id(db, output_id, str(current_user.id))
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    version = OutputVersionService.create_version(
        db=db,
        output_id=output_id,
        version_data=output.output_data
    )
    
    return VersionResponse.from_orm(version)


@router.get("/{output_id}/versions/{version_id}", response_model=VersionResponse)
async def get_output_version(
    output_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific version"""
    # Verify user owns the output
    output = OutputService.get_output_by_id(db, output_id, str(current_user.id))
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    version = OutputVersionService.get_version(db, output_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return VersionResponse.from_orm(version)


@router.post("/{output_id}/versions/{version_id}/restore", response_model=OutputResponse)
async def restore_output_version(
    output_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore output to a specific version"""
    db_output = OutputVersionService.restore_version(
        db=db,
        output_id=output_id,
        version_id=version_id,
        user_id=str(current_user.id)
    )
    
    if not db_output:
        raise HTTPException(status_code=404, detail="Output or version not found")
    
    return OutputResponse.from_orm(db_output)


@router.get("/{output_id}/versions/{version1_id}/diff/{version2_id}")
async def get_version_diff(
    output_id: str,
    version1_id: str,
    version2_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get diff between two versions"""
    # Verify user owns the output
    output = OutputService.get_output_by_id(db, output_id, str(current_user.id))
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    diff = OutputVersionService.get_version_diff(
        db=db,
        output_id=output_id,
        version1_id=version1_id,
        version2_id=version2_id
    )
    
    if not diff:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    return diff