from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.company import (
    CompanyProfile, 
    CompanyProfileCreate, 
    CompanyProfileUpdate,
    CompanyProfileList
)
from app.services.company_service import CompanyProfileService

router = APIRouter()


@router.post("/", response_model=CompanyProfile, status_code=status.HTTP_201_CREATED)
def create_company_profile(
    profile_data: CompanyProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new company profile"""
    return CompanyProfileService.create_profile(db, current_user, profile_data)


@router.get("/", response_model=CompanyProfileList)
def get_company_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all company profiles for the current user"""
    profiles = CompanyProfileService.get_user_profiles(db, current_user)
    return CompanyProfileList(profiles=profiles, total=len(profiles))


@router.get("/{profile_id}", response_model=CompanyProfile)
def get_company_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific company profile by ID"""
    profile = CompanyProfileService.get_profile_by_id(db, current_user, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    return profile


@router.put("/{profile_id}", response_model=CompanyProfile)
def update_company_profile(
    profile_id: UUID,
    profile_data: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a company profile"""
    profile = CompanyProfileService.update_profile(db, current_user, profile_id, profile_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a company profile"""
    success = CompanyProfileService.delete_profile(db, current_user, profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )


@router.get("/stats/summary")
def get_profile_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about user's company profiles"""
    return CompanyProfileService.get_profile_statistics(db, current_user)