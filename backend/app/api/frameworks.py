from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.framework import (
    Framework,
    FrameworkList,
    FrameworkContent,
    FrameworkCreate,
    FrameworkUpdate
)
from app.services.framework_service import FrameworkService, FrameworkContentService

router = APIRouter()


@router.get("/", response_model=FrameworkList)
async def list_frameworks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of frameworks with filtering and pagination.
    Free users only see non-premium frameworks.
    """
    # Filter based on user subscription
    is_premium_filter = None if current_user.subscription_tier == "premium" else False
    
    frameworks = FrameworkService.get_frameworks(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        difficulty_level=difficulty_level,
        is_premium=is_premium_filter,
        search=search
    )
    
    total = FrameworkService.count_frameworks(
        db=db,
        category=category,
        difficulty_level=difficulty_level,
        is_premium=is_premium_filter,
        search=search
    )
    
    return FrameworkList(
        frameworks=[Framework.from_orm(f) for f in frameworks],
        total=total,
        page=skip // limit + 1,
        limit=limit
    )


@router.get("/categories")
async def get_framework_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available framework categories"""
    categories = FrameworkService.get_framework_categories(db)
    return {"categories": categories}


@router.get("/difficulty-levels")
async def get_difficulty_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available difficulty levels"""
    levels = FrameworkService.get_framework_difficulty_levels(db)
    return {"difficulty_levels": levels}


@router.get("/free")
async def get_free_frameworks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get free frameworks (accessible without authentication)"""
    frameworks = FrameworkService.get_free_frameworks(db=db, skip=skip, limit=limit)
    total = FrameworkService.count_frameworks(db=db, is_premium=False)
    
    return FrameworkList(
        frameworks=[Framework.from_orm(f) for f in frameworks],
        total=total,
        page=skip // limit + 1,
        limit=limit
    )


@router.get("/{framework_id}", response_model=Framework)
async def get_framework(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single framework by ID"""
    framework = FrameworkService.get_framework_by_id(db, framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    # Check if user has access to premium framework
    if framework.is_premium and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=403, 
            detail="Premium subscription required to access this framework"
        )
    
    return Framework.from_orm(framework)


@router.get("/{framework_id}/content", response_model=FrameworkContent)
async def get_framework_content(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get framework content based on user subscription level"""
    content = FrameworkContentService.get_framework_content(
        db=db,
        framework_id=framework_id,
        user_subscription=current_user.subscription_tier
    )
    
    if not content:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return FrameworkContent(**content)


@router.get("/{framework_id}/steps")
async def get_framework_steps(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get framework completion steps"""
    framework = FrameworkService.get_framework_by_id(db, framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    # Check premium access
    if framework.is_premium and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=403, 
            detail="Premium subscription required to access this framework"
        )
    
    steps = FrameworkContentService.get_framework_steps(db, framework_id)
    return {"steps": steps or []}


@router.get("/{framework_id}/components")
async def get_framework_components(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get framework components/sections"""
    framework = FrameworkService.get_framework_by_id(db, framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    # Check premium access
    if framework.is_premium and current_user.subscription_tier != "premium":
        raise HTTPException(
            status_code=403, 
            detail="Premium subscription required to access this framework"
        )
    
    components = FrameworkContentService.get_framework_components(db, framework_id)
    return {"components": components or {}}


# Admin endpoints (for framework management)
@router.post("/", response_model=Framework)
async def create_framework(
    framework: FrameworkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new framework (admin only)"""
    # TODO: Add admin role check
    if current_user.subscription_tier != "premium":  # Temporary check
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_framework = FrameworkService.create_framework(db, framework)
    return Framework.from_orm(db_framework)


@router.put("/{framework_id}", response_model=Framework)
async def update_framework(
    framework_id: str,
    framework_update: FrameworkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a framework (admin only)"""
    # TODO: Add admin role check
    if current_user.subscription_tier != "premium":  # Temporary check
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_framework = FrameworkService.update_framework(db, framework_id, framework_update)
    if not db_framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return Framework.from_orm(db_framework)


@router.delete("/{framework_id}")
async def delete_framework(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a framework (admin only)"""
    # TODO: Add admin role check
    if current_user.subscription_tier != "premium":  # Temporary check
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = FrameworkService.delete_framework(db, framework_id)
    if not success:
        raise HTTPException(status_code=404, detail="Framework not found")
    
    return {"message": "Framework deleted successfully"}