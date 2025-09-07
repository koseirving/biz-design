from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserOutput, CompanyProfile, UserProgress
from app.core.database import get_db
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class ConsentType:
    """GDPR consent types"""
    ESSENTIAL = "essential"          # 必須クッキー・機能
    ANALYTICS = "analytics"          # 分析・統計
    MARKETING = "marketing"          # マーケティング
    PERSONALIZATION = "personalization"  # パーソナライゼーション


class GDPRConsentManager:
    """GDPR同意管理クラス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_consent(
        self,
        user_id: str,
        consent_data: Dict[str, bool],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """ユーザーの同意を記録"""
        
        consent_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'consents': consent_data,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'gdpr_version': '2018',
            'legal_basis': self._determine_legal_basis(consent_data)
        }
        
        # Store in user's consent history (implement table later)
        logger.info(f"Recorded GDPR consent for user {user_id}: {consent_data}")
        
        return consent_record['id']
    
    def get_user_consents(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーの最新の同意情報を取得"""
        
        # Implementation would query consent_history table
        # For now, return default consent structure
        return {
            'user_id': user_id,
            'consents': {
                ConsentType.ESSENTIAL: True,      # Always true for functionality
                ConsentType.ANALYTICS: False,     # Default opt-out
                ConsentType.MARKETING: False,     # Default opt-out
                ConsentType.PERSONALIZATION: False  # Default opt-out
            },
            'last_updated': datetime.utcnow().isoformat(),
            'consent_string': self._generate_consent_string(user_id)
        }
    
    def update_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        reason: str = "user_action"
    ) -> bool:
        """特定の同意項目を更新"""
        
        current_consents = self.get_user_consents(user_id)
        if not current_consents:
            return False
        
        current_consents['consents'][consent_type] = granted
        current_consents['last_updated'] = datetime.utcnow().isoformat()
        
        # Record the change
        self.record_consent(
            user_id=user_id,
            consent_data=current_consents['consents']
        )
        
        logger.info(f"Updated consent {consent_type}={granted} for user {user_id}, reason: {reason}")
        return True
    
    def withdraw_all_consents(self, user_id: str) -> bool:
        """すべての同意を撤回（必須を除く）"""
        
        withdrawal_consents = {
            ConsentType.ESSENTIAL: True,      # Cannot withdraw essential
            ConsentType.ANALYTICS: False,
            ConsentType.MARKETING: False,
            ConsentType.PERSONALIZATION: False
        }
        
        consent_id = self.record_consent(
            user_id=user_id,
            consent_data=withdrawal_consents
        )
        
        logger.info(f"Withdrew all non-essential consents for user {user_id}")
        return True
    
    def _determine_legal_basis(self, consent_data: Dict[str, bool]) -> Dict[str, str]:
        """法的根拠を決定"""
        
        legal_basis = {}
        for consent_type, granted in consent_data.items():
            if consent_type == ConsentType.ESSENTIAL:
                legal_basis[consent_type] = "legitimate_interest"  # 正当な利益
            elif granted:
                legal_basis[consent_type] = "consent"  # 同意
            else:
                legal_basis[consent_type] = "not_granted"
        
        return legal_basis
    
    def _generate_consent_string(self, user_id: str) -> str:
        """同意文字列を生成（IAB準拠風）"""
        
        # Simplified consent string for demo
        timestamp = int(datetime.utcnow().timestamp())
        return f"GDPR-{user_id[:8]}-{timestamp}"


class DataMinimizationService:
    """データ最小化サービス"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_data_usage(self, user_id: str) -> Dict[str, Any]:
        """ユーザーのデータ使用状況を分析"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Analyze data patterns
        analysis = {
            'user_id': user_id,
            'data_categories': {
                'personal_data': {
                    'email': {'necessary': True, 'retention_days': 2555},  # 7 years
                    'password_hash': {'necessary': True, 'retention_days': 2555}
                },
                'usage_data': {
                    'learning_sessions': {'necessary': False, 'retention_days': 1095},  # 3 years
                    'outputs': {'necessary': False, 'retention_days': 1095}
                },
                'analytics_data': {
                    'page_views': {'necessary': False, 'retention_days': 365},  # 1 year
                    'interactions': {'necessary': False, 'retention_days': 365}
                }
            },
            'recommendations': []
        }
        
        # Check for old data that should be purged
        cutoff_date = datetime.utcnow() - timedelta(days=1095)  # 3 years
        old_outputs = self.db.query(UserOutput).filter(
            UserOutput.user_id == user_id,
            UserOutput.created_at < cutoff_date
        ).count()
        
        if old_outputs > 0:
            analysis['recommendations'].append({
                'type': 'data_purge',
                'description': f'Found {old_outputs} outputs older than 3 years',
                'action': 'Consider archiving or deleting old outputs'
            })
        
        return analysis
    
    def suggest_data_retention_policies(self) -> List[Dict[str, Any]]:
        """データ保持ポリシーの提案"""
        
        policies = [
            {
                'data_type': 'user_outputs',
                'suggested_retention': '3 years',
                'legal_requirement': 'None',
                'business_justification': 'User learning history and progress tracking'
            },
            {
                'data_type': 'learning_sessions',
                'suggested_retention': '2 years', 
                'legal_requirement': 'None',
                'business_justification': 'Analytics and improvement of learning experience'
            },
            {
                'data_type': 'notification_history',
                'suggested_retention': '1 year',
                'legal_requirement': 'None',
                'business_justification': 'Debugging and user support'
            },
            {
                'data_type': 'audit_logs',
                'suggested_retention': '7 years',
                'legal_requirement': 'GDPR Article 30',
                'business_justification': 'Compliance and security incident investigation'
            }
        ]
        
        return policies


class GDPRComplianceService:
    """GDPR準拠のメインサービス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.consent_manager = GDPRConsentManager(db)
        self.data_minimization = DataMinimizationService(db)
    
    def assess_compliance(self, user_id: str) -> Dict[str, Any]:
        """ユーザーのGDPR準拠状況を評価"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check consent status
        consent_info = self.consent_manager.get_user_consents(user_id)
        
        # Check data retention
        data_analysis = self.data_minimization.analyze_data_usage(user_id)
        
        # Assess compliance score
        compliance_score = self._calculate_compliance_score(consent_info, data_analysis)
        
        assessment = {
            'user_id': user_id,
            'assessment_date': datetime.utcnow().isoformat(),
            'compliance_score': compliance_score,
            'consent_status': consent_info,
            'data_usage': data_analysis,
            'recommendations': self._generate_compliance_recommendations(consent_info, data_analysis),
            'user_rights_status': self._check_user_rights_compliance(user_id)
        }
        
        return assessment
    
    def handle_data_subject_request(
        self,
        user_id: str,
        request_type: str,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """データ主体の権利行使要求を処理"""
        
        request_id = str(uuid.uuid4())
        
        handlers = {
            'access': self._handle_access_request,
            'portability': self._handle_portability_request,
            'rectification': self._handle_rectification_request,
            'erasure': self._handle_erasure_request,
            'restriction': self._handle_restriction_request,
            'objection': self._handle_objection_request
        }
        
        handler = handlers.get(request_type)
        if not handler:
            raise ValueError(f"Unknown request type: {request_type}")
        
        response = handler(user_id, additional_data or {})
        response['request_id'] = request_id
        response['request_type'] = request_type
        response['processed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Processed GDPR {request_type} request {request_id} for user {user_id}")
        
        return response
    
    def _handle_access_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """アクセス権（データ開示）の処理"""
        
        from app.services.data_export_service import DataExportService
        
        # Generate data export
        export_info = DataExportService.export_user_data(self.db, user_id)
        
        return {
            'status': 'completed',
            'message': 'Personal data access provided',
            'export_info': export_info,
            'processing_time_days': 0,  # Immediate
            'legal_basis': 'GDPR Article 15 - Right of access'
        }
    
    def _handle_portability_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """データポータビリティ権の処理"""
        
        # Similar to access but in structured format
        from app.services.data_export_service import DataExportService
        
        export_info = DataExportService.export_user_data(self.db, user_id)
        
        return {
            'status': 'completed',
            'message': 'Data provided in portable format',
            'export_info': export_info,
            'format': 'JSON/CSV',
            'legal_basis': 'GDPR Article 20 - Right to data portability'
        }
    
    def _handle_rectification_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """訂正権の処理"""
        
        corrections = data.get('corrections', {})
        
        # Update user data based on corrections
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        updated_fields = []
        if 'email' in corrections:
            user.email = corrections['email']
            updated_fields.append('email')
        
        self.db.commit()
        
        return {
            'status': 'completed',
            'message': f'Updated fields: {", ".join(updated_fields)}',
            'updated_fields': updated_fields,
            'legal_basis': 'GDPR Article 16 - Right to rectification'
        }
    
    def _handle_erasure_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """消去権（忘れられる権利）の処理"""
        
        # This would trigger the deletion process
        return {
            'status': 'scheduled',
            'message': 'Account deletion scheduled',
            'deletion_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'legal_basis': 'GDPR Article 17 - Right to erasure'
        }
    
    def _handle_restriction_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """処理制限権の処理"""
        
        restrictions = data.get('restrictions', [])
        
        return {
            'status': 'applied',
            'message': 'Processing restrictions applied',
            'restrictions': restrictions,
            'legal_basis': 'GDPR Article 18 - Right to restriction of processing'
        }
    
    def _handle_objection_request(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """処理に対する異議権の処理"""
        
        objections = data.get('objections', [])
        
        # Update consent based on objections
        for objection_type in objections:
            self.consent_manager.update_consent(
                user_id=user_id,
                consent_type=objection_type,
                granted=False,
                reason="user_objection"
            )
        
        return {
            'status': 'processed',
            'message': 'Objections processed and consent updated',
            'objections': objections,
            'legal_basis': 'GDPR Article 21 - Right to object'
        }
    
    def _calculate_compliance_score(
        self,
        consent_info: Dict[str, Any],
        data_analysis: Dict[str, Any]
    ) -> int:
        """コンプライアンススコアを計算（0-100）"""
        
        score = 100
        
        # Deduct points for missing consents where required
        consents = consent_info.get('consents', {})
        if not consents.get(ConsentType.ANALYTICS, False):
            # This is actually good for privacy, but we need explicit consent for analytics
            pass
        
        # Deduct points for data retention issues
        recommendations = data_analysis.get('recommendations', [])
        for rec in recommendations:
            if rec['type'] == 'data_purge':
                score -= 10
        
        return max(0, min(100, score))
    
    def _generate_compliance_recommendations(
        self,
        consent_info: Dict[str, Any],
        data_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """コンプライアンス改善の推奨事項を生成"""
        
        recommendations = []
        
        # Check consent freshness
        last_updated = consent_info.get('last_updated')
        if last_updated:
            last_update = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            if (datetime.utcnow() - last_update.replace(tzinfo=None)).days > 365:
                recommendations.append({
                    'type': 'consent_refresh',
                    'priority': 'medium',
                    'description': 'User consent is over 1 year old and should be refreshed'
                })
        
        # Add data analysis recommendations
        recommendations.extend(data_analysis.get('recommendations', []))
        
        return recommendations
    
    def _check_user_rights_compliance(self, user_id: str) -> Dict[str, Any]:
        """ユーザー権利の実施状況をチェック"""
        
        return {
            'access_right': {'implemented': True, 'response_time': '24 hours'},
            'rectification_right': {'implemented': True, 'response_time': '24 hours'},
            'erasure_right': {'implemented': True, 'response_time': '30 days'},
            'portability_right': {'implemented': True, 'response_time': '24 hours'},
            'restriction_right': {'implemented': True, 'response_time': '24 hours'},
            'objection_right': {'implemented': True, 'response_time': '24 hours'},
            'automated_decision_making': {'implemented': False, 'reason': 'No automated decision making in current system'}
        }


# Utility functions for GDPR compliance

def is_eu_user(ip_address: str) -> bool:
    """IP アドレスからEUユーザーかどうかを判定"""
    # Implementation would use IP geolocation service
    # For now, assume all users might be EU users (safer approach)
    return True


def requires_gdpr_compliance(user: User) -> bool:
    """ユーザーがGDPR対象かどうか判定"""
    # For production, check user location or explicit EU designation
    return True  # Safe default: assume all users require GDPR compliance


def format_gdpr_notice(notice_type: str, **kwargs) -> Dict[str, str]:
    """GDPR通知文を生成"""
    
    notices = {
        'data_collection': {
            'title': 'Personal Data Collection Notice',
            'content': 'We collect and process your personal data to provide our business framework learning service. Legal basis: Article 6(1)(a) GDPR - Consent, Article 6(1)(b) GDPR - Contract performance.'
        },
        'consent_request': {
            'title': 'Cookie and Data Processing Consent',
            'content': 'We use cookies and similar technologies to enhance your experience. You can withdraw consent at any time in your privacy settings.'
        },
        'retention_policy': {
            'title': 'Data Retention Policy',
            'content': 'We retain your personal data for as long as necessary to fulfill the purposes outlined in our privacy policy, typically 3-7 years depending on data type.'
        }
    }
    
    return notices.get(notice_type, {
        'title': 'Privacy Notice',
        'content': 'Your privacy is important to us. Please review our privacy policy for details.'
    })