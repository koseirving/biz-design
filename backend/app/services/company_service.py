from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.user import CompanyProfile, User
from app.schemas.company import CompanyProfileCreate, CompanyProfileUpdate
from fastapi import HTTPException, status


class CompanyProfileService:
    """Service for managing company profiles (own company and competitors)"""
    
    @staticmethod
    def create_profile(
        db: Session, 
        user: User, 
        profile_data: CompanyProfileCreate
    ) -> CompanyProfile:
        """Create a new company profile for the user"""
        # Check if user already has a profile with this name
        existing = db.query(CompanyProfile).filter(
            and_(
                CompanyProfile.user_id == user.id,
                CompanyProfile.profile_name == profile_data.profile_name
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile with this name already exists"
            )
        
        db_profile = CompanyProfile(
            user_id=user.id,
            profile_name=profile_data.profile_name,
            profile_data=profile_data.profile_data
        )
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def get_user_profiles(db: Session, user: User) -> List[CompanyProfile]:
        """Get all company profiles for a user"""
        return db.query(CompanyProfile).filter(
            CompanyProfile.user_id == user.id
        ).order_by(CompanyProfile.created_at.desc()).all()
    
    @staticmethod
    def get_profile_by_id(
        db: Session, 
        user: User, 
        profile_id: UUID
    ) -> Optional[CompanyProfile]:
        """Get a specific company profile by ID (only if owned by user)"""
        return db.query(CompanyProfile).filter(
            and_(
                CompanyProfile.id == profile_id,
                CompanyProfile.user_id == user.id
            )
        ).first()
    
    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        profile_id: UUID,
        profile_data: CompanyProfileUpdate
    ) -> Optional[CompanyProfile]:
        """Update a company profile"""
        db_profile = CompanyProfileService.get_profile_by_id(db, user, profile_id)
        if not db_profile:
            return None
        
        # Check for duplicate name if name is being updated
        if profile_data.profile_name and profile_data.profile_name != db_profile.profile_name:
            existing = db.query(CompanyProfile).filter(
                and_(
                    CompanyProfile.user_id == user.id,
                    CompanyProfile.profile_name == profile_data.profile_name,
                    CompanyProfile.id != profile_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Profile with this name already exists"
                )
        
        # Update fields that were provided
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(db_profile, field, value)
        
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def delete_profile(
        db: Session,
        user: User,
        profile_id: UUID
    ) -> bool:
        """Delete a company profile"""
        db_profile = CompanyProfileService.get_profile_by_id(db, user, profile_id)
        if not db_profile:
            return False
        
        db.delete(db_profile)
        db.commit()
        return True
    
    @staticmethod
    def get_profile_statistics(db: Session, user: User) -> Dict[str, Any]:
        """Get statistics about user's company profiles"""
        profiles = CompanyProfileService.get_user_profiles(db, user)
        
        profile_types = {}
        for profile in profiles:
            if profile.profile_data and "type" in profile.profile_data:
                profile_type = profile.profile_data["type"]
                profile_types[profile_type] = profile_types.get(profile_type, 0) + 1
        
        return {
            "total_profiles": len(profiles),
            "profile_types": profile_types,
            "recent_profiles": profiles[:5]  # Last 5 profiles
        }