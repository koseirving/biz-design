import json
import csv
import uuid
import os
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.user import (
    User, UserOutput, CompanyProfile, UserProgress,
    UserLearningSession, NotificationPreferences, 
    NotificationHistory, UserBadge
)

class DataExportService:
    
    @staticmethod
    def export_user_data(db: Session, user_id: str) -> Dict[str, str]:
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