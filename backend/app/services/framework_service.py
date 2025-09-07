from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import BusinessFramework
from app.schemas.framework import FrameworkCreate, FrameworkUpdate
import uuid


class FrameworkService:
    
    @staticmethod
    def get_framework_by_id(db: Session, framework_id: str) -> Optional[BusinessFramework]:
        """Get a single framework by ID"""
        return db.query(BusinessFramework).filter(BusinessFramework.id == framework_id).first()
    
    @staticmethod
    def get_frameworks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_premium: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[BusinessFramework]:
        """Get frameworks with filtering and pagination"""
        query = db.query(BusinessFramework)
        
        # Apply filters
        if category:
            query = query.filter(BusinessFramework.category == category)
        
        if difficulty_level:
            query = query.filter(BusinessFramework.difficulty_level == difficulty_level)
        
        if is_premium is not None:
            query = query.filter(BusinessFramework.is_premium == is_premium)
        
        if search:
            search_filter = or_(
                BusinessFramework.name.ilike(f"%{search}%"),
                BusinessFramework.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_frameworks(
        db: Session,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_premium: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Count frameworks with filters"""
        query = db.query(BusinessFramework)
        
        # Apply same filters as get_frameworks
        if category:
            query = query.filter(BusinessFramework.category == category)
        
        if difficulty_level:
            query = query.filter(BusinessFramework.difficulty_level == difficulty_level)
        
        if is_premium is not None:
            query = query.filter(BusinessFramework.is_premium == is_premium)
        
        if search:
            search_filter = or_(
                BusinessFramework.name.ilike(f"%{search}%"),
                BusinessFramework.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.count()
    
    @staticmethod
    def create_framework(db: Session, framework: FrameworkCreate) -> BusinessFramework:
        """Create a new framework"""
        db_framework = BusinessFramework(
            id=uuid.uuid4(),
            name=framework.name,
            description=framework.description,
            category=framework.category,
            difficulty_level=framework.difficulty_level,
            estimated_duration=framework.estimated_duration,
            is_premium=framework.is_premium,
            micro_content=framework.micro_content
        )
        db.add(db_framework)
        db.commit()
        db.refresh(db_framework)
        return db_framework
    
    @staticmethod
    def update_framework(
        db: Session, 
        framework_id: str, 
        framework_update: FrameworkUpdate
    ) -> Optional[BusinessFramework]:
        """Update an existing framework"""
        db_framework = FrameworkService.get_framework_by_id(db, framework_id)
        if not db_framework:
            return None
        
        update_data = framework_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_framework, field, value)
        
        db.commit()
        db.refresh(db_framework)
        return db_framework
    
    @staticmethod
    def delete_framework(db: Session, framework_id: str) -> bool:
        """Delete a framework"""
        db_framework = FrameworkService.get_framework_by_id(db, framework_id)
        if not db_framework:
            return False
        
        db.delete(db_framework)
        db.commit()
        return True
    
    @staticmethod
    def get_framework_categories(db: Session) -> List[str]:
        """Get all unique framework categories"""
        categories = db.query(BusinessFramework.category).distinct().all()
        return [category[0] for category in categories]
    
    @staticmethod
    def get_framework_difficulty_levels(db: Session) -> List[str]:
        """Get all unique difficulty levels"""
        levels = db.query(BusinessFramework.difficulty_level).distinct().all()
        return [level[0] for level in levels]
    
    @staticmethod
    def get_free_frameworks(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessFramework]:
        """Get only free frameworks for non-premium users"""
        return db.query(BusinessFramework).filter(
            BusinessFramework.is_premium == False
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_premium_frameworks(db: Session, skip: int = 0, limit: int = 100) -> List[BusinessFramework]:
        """Get only premium frameworks"""
        return db.query(BusinessFramework).filter(
            BusinessFramework.is_premium == True
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_framework_by_name(db: Session, name: str) -> Optional[BusinessFramework]:
        """Get framework by name (useful for seeding)"""
        return db.query(BusinessFramework).filter(BusinessFramework.name == name).first()


class FrameworkContentService:
    """Service for handling framework content and learning materials"""
    
    @staticmethod
    def get_framework_content(db: Session, framework_id: str, user_subscription: str = "free") -> Optional[Dict[str, Any]]:
        """Get framework content based on user subscription level"""
        framework = FrameworkService.get_framework_by_id(db, framework_id)
        
        if not framework:
            return None
        
        # Check if user has access to this framework
        if framework.is_premium and user_subscription == "free":
            # Return limited content for free users
            return {
                "id": str(framework.id),
                "name": framework.name,
                "description": framework.description,
                "category": framework.category,
                "difficulty_level": framework.difficulty_level,
                "estimated_duration": framework.estimated_duration,
                "is_premium": framework.is_premium,
                "content_preview": framework.micro_content.get("overview", "") if framework.micro_content else "",
                "access_level": "preview"
            }
        
        # Return full content for premium users or free frameworks
        return {
            "id": str(framework.id),
            "name": framework.name,
            "description": framework.description,
            "category": framework.category,
            "difficulty_level": framework.difficulty_level,
            "estimated_duration": framework.estimated_duration,
            "is_premium": framework.is_premium,
            "micro_content": framework.micro_content,
            "access_level": "full"
        }
    
    @staticmethod
    def get_framework_steps(db: Session, framework_id: str) -> Optional[List[str]]:
        """Get the steps for completing a framework"""
        framework = FrameworkService.get_framework_by_id(db, framework_id)
        
        if not framework or not framework.micro_content:
            return None
        
        return framework.micro_content.get("steps", [])
    
    @staticmethod
    def get_framework_components(db: Session, framework_id: str) -> Optional[Dict[str, Any]]:
        """Get the components/sections of a framework"""
        framework = FrameworkService.get_framework_by_id(db, framework_id)
        
        if not framework or not framework.micro_content:
            return None
        
        return framework.micro_content.get("components", {})