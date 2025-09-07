from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import UserOutput, OutputVersions
from datetime import datetime
import uuid
import json


class OutputService:
    
    @staticmethod
    def get_output_by_id(db: Session, output_id: str, user_id: str) -> Optional[UserOutput]:
        """Get output by ID and user ID for security"""
        return db.query(UserOutput).filter(
            UserOutput.id == output_id,
            UserOutput.user_id == user_id
        ).first()
    
    @staticmethod
    def get_user_outputs(
        db: Session, 
        user_id: str, 
        framework_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserOutput]:
        """Get user's outputs with optional framework filtering"""
        query = db.query(UserOutput).filter(UserOutput.user_id == user_id)
        
        if framework_id:
            query = query.filter(UserOutput.framework_id == framework_id)
        
        return query.order_by(desc(UserOutput.updated_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_output(
        db: Session, 
        user_id: str, 
        framework_id: str, 
        output_data: Dict[str, Any],
        auto_version: bool = True
    ) -> UserOutput:
        """Create a new output"""
        db_output = UserOutput(
            id=uuid.uuid4(),
            user_id=user_id,
            framework_id=framework_id,
            output_data=output_data
        )
        db.add(db_output)
        db.commit()
        db.refresh(db_output)
        
        # Create initial version if auto_version is enabled
        if auto_version:
            OutputVersionService.create_version(db, str(db_output.id), output_data, is_current=True)
        
        return db_output
    
    @staticmethod
    def update_output(
        db: Session, 
        output_id: str, 
        user_id: str, 
        output_data: Dict[str, Any],
        create_version: bool = False
    ) -> Optional[UserOutput]:
        """Update an existing output"""
        db_output = OutputService.get_output_by_id(db, output_id, user_id)
        if not db_output:
            return None
        
        # Create version before updating if requested
        if create_version:
            OutputVersionService.create_version(db, output_id, db_output.output_data)
        
        db_output.output_data = output_data
        db_output.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_output)
        
        # Update the current version
        OutputVersionService.update_current_version(db, output_id, output_data)
        
        return db_output
    
    @staticmethod
    def delete_output(db: Session, output_id: str, user_id: str) -> bool:
        """Delete an output and all its versions"""
        db_output = OutputService.get_output_by_id(db, output_id, user_id)
        if not db_output:
            return False
        
        # Delete all versions first
        OutputVersionService.delete_all_versions(db, output_id)
        
        # Delete the output
        db.delete(db_output)
        db.commit()
        return True
    
    @staticmethod
    def auto_save_output(
        db: Session, 
        output_id: str, 
        user_id: str, 
        output_data: Dict[str, Any]
    ) -> Optional[UserOutput]:
        """Auto-save output (used for draft saving every 30 seconds)"""
        db_output = OutputService.get_output_by_id(db, output_id, user_id)
        if not db_output:
            return None
        
        db_output.output_data = output_data
        db_output.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_output)
        return db_output


class OutputVersionService:
    
    @staticmethod
    def get_versions(db: Session, output_id: str) -> List[OutputVersions]:
        """Get all versions of an output"""
        return db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id
        ).order_by(desc(OutputVersions.version_number)).all()
    
    @staticmethod
    def get_version(db: Session, output_id: str, version_id: str) -> Optional[OutputVersions]:
        """Get a specific version"""
        return db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id,
            OutputVersions.id == version_id
        ).first()
    
    @staticmethod
    def create_version(
        db: Session, 
        output_id: str, 
        version_data: Dict[str, Any],
        is_current: bool = False
    ) -> OutputVersions:
        """Create a new version"""
        # Get the next version number
        latest_version = db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id
        ).order_by(desc(OutputVersions.version_number)).first()
        
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Mark all other versions as not current if this is the current version
        if is_current:
            db.query(OutputVersions).filter(
                OutputVersions.output_id == output_id
            ).update({"is_current": False})
        
        db_version = OutputVersions(
            id=uuid.uuid4(),
            output_id=output_id,
            version_number=version_number,
            version_data=version_data,
            is_current=is_current
        )
        
        db.add(db_version)
        db.commit()
        db.refresh(db_version)
        
        # Keep only last 10 versions
        OutputVersionService._cleanup_old_versions(db, output_id)
        
        return db_version
    
    @staticmethod
    def restore_version(
        db: Session, 
        output_id: str, 
        version_id: str,
        user_id: str
    ) -> Optional[UserOutput]:
        """Restore output to a specific version"""
        version = OutputVersionService.get_version(db, output_id, version_id)
        if not version:
            return None
        
        # Update the main output
        db_output = OutputService.get_output_by_id(db, output_id, user_id)
        if not db_output:
            return None
        
        # Create a new version with current data before restoring
        OutputVersionService.create_version(db, output_id, db_output.output_data)
        
        # Restore the data
        db_output.output_data = version.version_data
        db_output.updated_at = datetime.utcnow()
        
        # Mark this version as current
        db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id
        ).update({"is_current": False})
        
        version.is_current = True
        
        db.commit()
        db.refresh(db_output)
        return db_output
    
    @staticmethod
    def get_version_diff(
        db: Session, 
        output_id: str, 
        version1_id: str, 
        version2_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get diff between two versions"""
        version1 = OutputVersionService.get_version(db, output_id, version1_id)
        version2 = OutputVersionService.get_version(db, output_id, version2_id)
        
        if not version1 or not version2:
            return None
        
        return {
            "version1": {
                "id": str(version1.id),
                "version_number": version1.version_number,
                "created_at": version1.created_at.isoformat(),
                "data": version1.version_data
            },
            "version2": {
                "id": str(version2.id),
                "version_number": version2.version_number,
                "created_at": version2.created_at.isoformat(),
                "data": version2.version_data
            },
            "diff": OutputVersionService._calculate_diff(version1.version_data, version2.version_data)
        }
    
    @staticmethod
    def update_current_version(db: Session, output_id: str, version_data: Dict[str, Any]):
        """Update the current version with new data"""
        current_version = db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id,
            OutputVersions.is_current == True
        ).first()
        
        if current_version:
            current_version.version_data = version_data
            db.commit()
    
    @staticmethod
    def delete_all_versions(db: Session, output_id: str):
        """Delete all versions for an output"""
        db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id
        ).delete()
        db.commit()
    
    @staticmethod
    def _cleanup_old_versions(db: Session, output_id: str, keep_count: int = 10):
        """Keep only the most recent N versions"""
        versions = db.query(OutputVersions).filter(
            OutputVersions.output_id == output_id
        ).order_by(desc(OutputVersions.version_number)).all()
        
        if len(versions) > keep_count:
            versions_to_delete = versions[keep_count:]
            for version in versions_to_delete:
                if not version.is_current:  # Never delete current version
                    db.delete(version)
            db.commit()
    
    @staticmethod
    def _calculate_diff(data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate diff between two data structures"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # Simple diff calculation - can be enhanced with proper diff libraries
        all_keys = set(data1.keys()) | set(data2.keys())
        
        for key in all_keys:
            if key not in data1:
                diff["added"][key] = data2[key]
            elif key not in data2:
                diff["removed"][key] = data1[key]
            elif data1[key] != data2[key]:
                diff["modified"][key] = {
                    "old": data1[key],
                    "new": data2[key]
                }
        
        return diff