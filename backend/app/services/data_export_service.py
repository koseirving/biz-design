import json
import csv
import uuid
import os
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import (
    User, UserOutput, CompanyProfile, UserProgress,
    UserLearningSession, NotificationPreferences, 
    NotificationHistory, UserBadge
)
import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

class ExportFormat:
    """Export format constants"""
    JSON = "json"
    CSV = "csv" 
    XML = "xml"
    PDF = "pdf"
    ZIP = "zip"


class ExportStatus:
    """Export status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DataExportService:
    
    def __init__(self, storage_backend: str = "local"):
        self.storage_backend = storage_backend
        self.exports_dir = Path("/tmp/exports")
        self.exports_dir.mkdir(exist_ok=True)
        
        # In production, initialize GCS client
        self.gcs_client = None
        self.gcs_bucket = None
        
    def create_export_request(self, db: Session, user_id: str, formats: List[str] = None) -> Dict[str, str]:
        """Create a new export request and return tracking information"""
        
        if formats is None:
            formats = [ExportFormat.JSON, ExportFormat.CSV]
        
        export_id = str(uuid.uuid4())
        request_timestamp = datetime.utcnow()
        
        # Store export request metadata (in production, use database table)
        export_metadata = {
            'export_id': export_id,
            'user_id': user_id,
            'formats': formats,
            'status': ExportStatus.PENDING,
            'created_at': request_timestamp.isoformat(),
            'expires_at': (request_timestamp + timedelta(days=7)).isoformat(),
            'download_urls': {},
            'file_sizes': {},
            'checksum': {}
        }
        
        logger.info(f"Created export request {export_id} for user {user_id}")
        
        # In production, store in database and process asynchronously
        return self._process_export_request(db, export_metadata)
    
    def _process_export_request(self, db: Session, export_metadata: Dict[str, Any]) -> Dict[str, str]:
        """Process the export request and generate files"""
        
        try:
            export_metadata['status'] = ExportStatus.PROCESSING
            
            user_id = export_metadata['user_id']
            export_id = export_metadata['export_id']
            formats = export_metadata['formats']
            
            # Collect user data
            user_data = self._collect_user_data(db, user_id)
            
            # Generate files for each requested format
            generated_files = {}
            
            for format_type in formats:
                if format_type == ExportFormat.JSON:
                    content = self._generate_json_export(user_data)
                    filename = f"user_data_export_{export_id}.json"
                    
                elif format_type == ExportFormat.CSV:
                    content = self._generate_csv_export(user_data)
                    filename = f"user_data_export_{export_id}.csv"
                    
                elif format_type == ExportFormat.XML:
                    content = self._generate_xml_export(user_data)
                    filename = f"user_data_export_{export_id}.xml"
                    
                elif format_type == ExportFormat.PDF:
                    content = self._generate_pdf_export(user_data)
                    filename = f"user_data_export_{export_id}.pdf"
                    
                else:
                    continue
                
                # Save file and get metadata
                file_info = self._save_export_file(filename, content)
                generated_files[format_type] = file_info
            
            # Create ZIP archive if multiple formats
            if len(formats) > 1:
                zip_info = self._create_zip_archive(export_id, generated_files)
                generated_files[ExportFormat.ZIP] = zip_info
            
            # Update export metadata
            export_metadata['status'] = ExportStatus.COMPLETED
            export_metadata['completed_at'] = datetime.utcnow().isoformat()
            export_metadata['files'] = generated_files
            
            # Generate download URLs
            download_urls = {}
            for format_type, file_info in generated_files.items():
                download_urls[format_type] = f"/api/users/download/{file_info['filename']}"
            
            export_metadata['download_urls'] = download_urls
            
            logger.info(f"Completed export request {export_id} for user {user_id}")
            
            return {
                'export_id': export_id,
                'status': ExportStatus.COMPLETED,
                'download_urls': download_urls,
                'expires_at': export_metadata['expires_at'],
                'formats': formats,
                'total_files': len(generated_files)
            }
            
        except Exception as e:
            export_metadata['status'] = ExportStatus.FAILED
            export_metadata['error'] = str(e)
            logger.error(f"Failed to process export request {export_metadata['export_id']}: {str(e)}")
            
            return {
                'export_id': export_metadata['export_id'],
                'status': ExportStatus.FAILED,
                'error': str(e)
            }
    
    def _save_export_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Save export file to storage backend"""
        
        file_path = self.exports_dir / filename
        
        # Calculate file size and checksum
        content_bytes = content.encode('utf-8') if isinstance(content, str) else content
        file_size = len(content_bytes)
        
        import hashlib
        checksum = hashlib.sha256(content_bytes).hexdigest()
        
        # Save to local storage (in production, save to GCS)
        if self.storage_backend == "local":
            with open(file_path, 'wb' if isinstance(content_bytes, bytes) else 'w') as f:
                f.write(content_bytes if isinstance(content_bytes, bytes) else content)
        
        # In production, upload to Google Cloud Storage
        # elif self.storage_backend == "gcs":
        #     blob = self.gcs_bucket.blob(f"exports/{filename}")
        #     blob.upload_from_string(content_bytes)
        
        return {
            'filename': filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'checksum': checksum,
            'created_at': datetime.utcnow().isoformat(),
            'storage_backend': self.storage_backend
        }
    
    def _create_zip_archive(self, export_id: str, files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create ZIP archive containing all export files"""
        
        zip_filename = f"user_data_export_{export_id}.zip"
        zip_path = self.exports_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for format_type, file_info in files.items():
                if format_type != ExportFormat.ZIP:  # Don't include ZIP in ZIP
                    file_path = Path(file_info['file_path'])
                    if file_path.exists():
                        zip_file.write(file_path, file_path.name)
        
        # Get ZIP file metadata
        zip_size = zip_path.stat().st_size
        
        with open(zip_path, 'rb') as f:
            import hashlib
            zip_checksum = hashlib.sha256(f.read()).hexdigest()
        
        return {
            'filename': zip_filename,
            'file_path': str(zip_path),
            'file_size': zip_size,
            'checksum': zip_checksum,
            'created_at': datetime.utcnow().isoformat(),
            'storage_backend': self.storage_backend,
            'contains_files': list(files.keys())
        }
    
    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """Get status of an export request"""
        
        # In production, query from database
        # For now, return mock status
        return {
            'export_id': export_id,
            'status': ExportStatus.COMPLETED,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'progress': 100
        }
    
    def cleanup_expired_exports(self) -> int:
        """Clean up expired export files"""
        
        cleaned_count = 0
        
        # Get all export files older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        for file_path in self.exports_dir.glob("user_data_export_*"):
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up expired export file: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Failed to clean up file {file_path}: {str(e)}")
        
        return cleaned_count
    
    @staticmethod
    def export_user_data(db: Session, user_id: str) -> Dict[str, str]:
        """Legacy method for backward compatibility"""
        service = DataExportService()
        return service.create_export_request(db, user_id)
        """Export all user data in JSON and CSV formats"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Collect all user data
        user_data = DataExportService._collect_user_data(db, user_id)
        
        # Generate export files
        json_content = DataExportService._generate_json_export(user_data)
        csv_content = DataExportService._generate_csv_export(user_data)
        
        # Create temporary file paths (in production, use cloud storage)
        export_id = str(uuid.uuid4())
        json_filename = f"user_data_export_{export_id}.json"
        csv_filename = f"user_data_export_{export_id}.csv"
        
        # Save files (in production, save to cloud storage)
        exports_dir = "/tmp/exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        json_path = os.path.join(exports_dir, json_filename)
        csv_path = os.path.join(exports_dir, csv_filename)
        
        with open(json_path, 'w') as f:
            f.write(json_content)
        
        with open(csv_path, 'w') as f:
            f.write(csv_content)
        
        # Generate download URLs (expires in 7 days)
        expiry_time = datetime.utcnow() + timedelta(days=7)
        
        return {
            "json_download_url": f"/api/download/{json_filename}",
            "csv_download_url": f"/api/download/{csv_filename}",
            "expires_at": expiry_time.isoformat(),
            "export_id": export_id
        }
    
    @staticmethod
    def _collect_user_data(db: Session, user_id: str) -> Dict[str, Any]:
        """Collect all user data from database"""
        
        # User profile
        user = db.query(User).filter(User.id == user_id).first()
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_active": user.is_active
        }
        
        # User outputs
        outputs = db.query(UserOutput).filter(UserOutput.user_id == user_id).all()
        outputs_data = [{
            "id": str(output.id),
            "framework_id": str(output.framework_id),
            "output_data": output.output_data,
            "created_at": output.created_at.isoformat() if output.created_at else None,
            "updated_at": output.updated_at.isoformat() if output.updated_at else None
        } for output in outputs]
        
        # Company profiles
        profiles = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).all()
        profiles_data = [{
            "id": str(profile.id),
            "profile_name": profile.profile_name,
            "profile_data": profile.profile_data,
            "created_at": profile.created_at.isoformat() if profile.created_at else None
        } for profile in profiles]
        
        # User progress
        progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
        progress_data = [{
            "id": str(p.id),
            "event_type": p.event_type,
            "entity_id": str(p.entity_id) if p.entity_id else None,
            "points_awarded": p.points_awarded,
            "metadata": p.metadata,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in progress]
        
        # Learning sessions
        sessions = db.query(UserLearningSession).filter(UserLearningSession.user_id == user_id).all()
        sessions_data = [{
            "id": str(session.id),
            "framework_id": str(session.framework_id),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "learning_data": session.learning_data,
            "status": session.status
        } for session in sessions]
        
        # Notification preferences
        prefs = db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user_id).first()
        prefs_data = None
        if prefs:
            prefs_data = {
                "id": str(prefs.id),
                "email_enabled": prefs.email_enabled,
                "push_enabled": prefs.push_enabled,
                "reminder_settings": prefs.reminder_settings,
                "updated_at": prefs.updated_at.isoformat() if prefs.updated_at else None
            }
        
        # Notification history
        notifications = db.query(NotificationHistory).filter(NotificationHistory.user_id == user_id).all()
        notifications_data = [{
            "id": str(notif.id),
            "notification_type": notif.notification_type,
            "delivery_channel": notif.delivery_channel,
            "content": notif.content,
            "scheduled_at": notif.scheduled_at.isoformat() if notif.scheduled_at else None,
            "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
            "status": notif.status
        } for notif in notifications]
        
        # User badges
        badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
        badges_data = [{
            "id": str(badge.id),
            "badge_type": badge.badge_type,
            "badge_name": badge.badge_name,
            "badge_metadata": badge.badge_metadata,
            "earned_at": badge.earned_at.isoformat() if badge.earned_at else None
        } for badge in badges]
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "user_profile": user_data,
            "outputs": outputs_data,
            "company_profiles": profiles_data,
            "progress": progress_data,
            "learning_sessions": sessions_data,
            "notification_preferences": prefs_data,
            "notification_history": notifications_data,
            "badges": badges_data
        }
    
    @staticmethod
    def _generate_json_export(user_data: Dict[str, Any]) -> str:
        """Generate JSON export"""
        return json.dumps(user_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _generate_csv_export(user_data: Dict[str, Any]) -> str:
        """Generate CSV export with flattened data"""
        output = StringIO()
        
        # Write user profile
        output.write("=== USER PROFILE ===\n")
        profile_writer = csv.DictWriter(output, fieldnames=user_data["user_profile"].keys())
        profile_writer.writeheader()
        profile_writer.writerow(user_data["user_profile"])
        output.write("\n")
        
        # Write outputs
        if user_data["outputs"]:
            output.write("=== USER OUTPUTS ===\n")
            outputs_writer = csv.DictWriter(output, fieldnames=user_data["outputs"][0].keys())
            outputs_writer.writeheader()
            for output_data in user_data["outputs"]:
                # Flatten JSON fields for CSV
                flattened = {k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                           for k, v in output_data.items()}
                outputs_writer.writerow(flattened)
            output.write("\n")
        
        # Write company profiles
        if user_data["company_profiles"]:
            output.write("=== COMPANY PROFILES ===\n")
            profiles_writer = csv.DictWriter(output, fieldnames=user_data["company_profiles"][0].keys())
            profiles_writer.writeheader()
            for profile in user_data["company_profiles"]:
                flattened = {k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                           for k, v in profile.items()}
                profiles_writer.writerow(flattened)
            output.write("\n")
        
        # Write progress data
        if user_data["progress"]:
            output.write("=== PROGRESS DATA ===\n")
            progress_writer = csv.DictWriter(output, fieldnames=user_data["progress"][0].keys())
            progress_writer.writeheader()
            for progress in user_data["progress"]:
                flattened = {k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                           for k, v in progress.items()}
                progress_writer.writerow(flattened)
            output.write("\n")
        
        return output.getvalue()
    
    def _generate_xml_export(self, user_data: Dict[str, Any]) -> str:
        """Generate XML export"""
        
        def dict_to_xml(data, parent_tag="data"):
            xml_parts = [f"<{parent_tag}>"]
            
            for key, value in data.items():
                if isinstance(value, dict):
                    xml_parts.append(dict_to_xml(value, key))
                elif isinstance(value, list):
                    xml_parts.append(f"<{key}>")
                    for item in value:
                        if isinstance(item, dict):
                            xml_parts.append(dict_to_xml(item, "item"))
                        else:
                            xml_parts.append(f"<item>{self._xml_escape(str(item))}</item>")
                    xml_parts.append(f"</{key}>")
                else:
                    xml_parts.append(f"<{key}>{self._xml_escape(str(value))}</{key}>")
            
            xml_parts.append(f"</{parent_tag}>")
            return "\n".join(xml_parts)
        
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content = dict_to_xml(user_data, "user_export")
        
        return xml_header + xml_content
    
    def _xml_escape(self, text: str) -> str:
        """Escape special characters for XML"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&apos;"))
    
    def _generate_pdf_export(self, user_data: Dict[str, Any]) -> bytes:
        """Generate PDF export (simplified version)"""
        
        # For full PDF generation, would use libraries like reportlab
        # This is a simplified version that generates a PDF-like structure
        
        pdf_content = f"""
        USER DATA EXPORT - PDF FORMAT
        ============================
        
        Export Date: {user_data.get('export_timestamp', 'Unknown')}
        
        USER PROFILE:
        {json.dumps(user_data.get('user_profile', {}), indent=2)}
        
        OUTPUTS:
        {json.dumps(user_data.get('outputs', []), indent=2)}
        
        COMPANY PROFILES:
        {json.dumps(user_data.get('company_profiles', []), indent=2)}
        
        PROGRESS DATA:
        {json.dumps(user_data.get('progress', []), indent=2)}
        
        LEARNING SESSIONS:
        {json.dumps(user_data.get('learning_sessions', []), indent=2)}
        
        NOTIFICATION PREFERENCES:
        {json.dumps(user_data.get('notification_preferences', {}), indent=2)}
        
        BADGES:
        {json.dumps(user_data.get('badges', []), indent=2)}
        
        ---
        Generated by GDPR-compliant data export system
        """
        
        return pdf_content.encode('utf-8')