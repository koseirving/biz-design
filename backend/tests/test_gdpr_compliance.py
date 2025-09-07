import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.gdpr_compliance_service import GDPRComplianceService
from app.models.user import User


class TestGDPRCompliance:
    """Test GDPR compliance functionality."""
    
    def test_record_consent_success(self, test_client, auth_headers, sample_gdpr_consent):
        """Test successful consent recording."""
        response = test_client.post(
            "/gdpr/consent/record",
            json=sample_gdpr_consent,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Consent recorded successfully"
        assert "consent_id" in data
        assert data["consent_types"] == sample_gdpr_consent["consent_types"]
    
    def test_record_consent_invalid_data(self, test_client, auth_headers):
        """Test consent recording with invalid data."""
        invalid_consent = {
            "consent_types": [],  # Empty consent types
            "legal_basis": "invalid_basis",
            "purpose": ""
        }
        
        response = test_client.post(
            "/gdpr/consent/record",
            json=invalid_consent,
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_withdraw_consent_success(self, test_client, auth_headers):
        """Test successful consent withdrawal."""
        # First record consent
        consent_data = {
            "consent_types": ["marketing"],
            "legal_basis": "consent",
            "purpose": "Marketing communications"
        }
        
        record_response = test_client.post(
            "/gdpr/consent/record",
            json=consent_data,
            headers=auth_headers
        )
        consent_id = record_response.json()["consent_id"]
        
        # Then withdraw it
        response = test_client.post(
            f"/gdpr/consent/withdraw/{consent_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Consent withdrawn successfully"
    
    def test_get_consent_history(self, test_client, auth_headers):
        """Test getting consent history."""
        response = test_client.get(
            "/gdpr/consent/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "consent_history" in data
        assert isinstance(data["consent_history"], list)
    
    def test_data_subject_rights_request(self, test_client, auth_headers):
        """Test data subject rights request."""
        request_data = {
            "right_type": "access",
            "description": "I want to access my personal data"
        }
        
        response = test_client.post(
            "/gdpr/data-subject-rights",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Data subject rights request submitted"
        assert "request_id" in data
    
    def test_privacy_notice(self, test_client):
        """Test getting privacy notice."""
        response = test_client.get("/gdpr/privacy-notice")
        
        assert response.status_code == 200
        data = response.json()
        assert "privacy_notice" in data
        assert "last_updated" in data
        assert "version" in data
    
    def test_compliance_assessment(self, test_client, premium_auth_headers):
        """Test compliance assessment (premium feature)."""
        response = test_client.post(
            "/gdpr/compliance/assessment",
            json={"assessment_type": "full"},
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "compliance_score" in data
        assert "recommendations" in data
    
    def test_compliance_assessment_unauthorized(self, test_client, auth_headers):
        """Test compliance assessment without premium access."""
        response = test_client.post(
            "/gdpr/compliance/assessment",
            json={"assessment_type": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_data_minimization_analysis(self, test_client, premium_auth_headers):
        """Test data minimization analysis."""
        response = test_client.get(
            "/gdpr/data-minimization/analysis",
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "recommendations" in data
    
    @patch('app.services.gdpr_compliance_service.GDPRComplianceService')
    def test_consent_manager_integration(self, mock_service, db_session, test_user):
        """Test GDPR service integration."""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Test consent recording
        mock_service_instance.consent_manager.record_consent.return_value = {
            "consent_id": "test-consent-id",
            "status": "recorded"
        }
        
        service = GDPRComplianceService(db_session)
        result = service.consent_manager.record_consent(
            user_id=str(test_user.id),
            consent_types=["marketing"],
            legal_basis="consent"
        )
        
        assert result["consent_id"] == "test-consent-id"
        assert result["status"] == "recorded"


class TestGDPRService:
    """Test GDPR service methods directly."""
    
    def test_gdpr_compliance_service_initialization(self, db_session):
        """Test GDPR service initialization."""
        service = GDPRComplianceService(db_session)
        
        assert service.db == db_session
        assert service.consent_manager is not None
        assert service.data_minimization is not None
    
    def test_validate_consent_types(self):
        """Test consent type validation."""
        from app.services.gdpr_compliance_service import GDPRConsentManager
        
        # Valid consent types
        valid_types = ["marketing", "analytics", "essential"]
        assert GDPRConsentManager._validate_consent_types(valid_types) is True
        
        # Invalid consent types
        invalid_types = ["invalid_type", "marketing"]
        assert GDPRConsentManager._validate_consent_types(invalid_types) is False
    
    def test_calculate_retention_period(self):
        """Test retention period calculation."""
        from app.services.gdpr_compliance_service import DataMinimizationService
        
        # Test different data categories
        assert DataMinimizationService._calculate_retention_period("profile_data") == 365 * 7  # 7 years
        assert DataMinimizationService._calculate_retention_period("marketing_data") == 365 * 2  # 2 years
        assert DataMinimizationService._calculate_retention_period("analytics_data") == 365 * 3  # 3 years
        assert DataMinimizationService._calculate_retention_period("unknown_category") == 365 * 7  # Default
    
    @patch('app.services.gdpr_compliance_service.datetime')
    def test_consent_expiry_check(self, mock_datetime):
        """Test consent expiry checking."""
        from app.services.gdpr_compliance_service import GDPRConsentManager
        
        # Mock current time
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        # Test expired consent
        consent_date = datetime(2022, 1, 1, 12, 0, 0)  # 2 years ago
        assert GDPRConsentManager._is_consent_expired(consent_date) is True
        
        # Test valid consent
        consent_date = datetime(2023, 6, 1, 12, 0, 0)  # 6 months ago
        assert GDPRConsentManager._is_consent_expired(consent_date) is False


class TestGDPRIntegration:
    """Test GDPR integration with other systems."""
    
    def test_gdpr_audit_logging(self, test_client, auth_headers, sample_gdpr_consent):
        """Test that GDPR actions are properly audited."""
        with patch('app.services.audit_log_service.audit_logger') as mock_audit:
            response = test_client.post(
                "/gdpr/consent/record",
                json=sample_gdpr_consent,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            # Verify audit logging was called
            mock_audit.log_event.assert_called()
    
    def test_gdpr_data_export_integration(self, test_client, auth_headers):
        """Test GDPR compliance with data export."""
        response = test_client.get(
            "/gdpr/data-export-compliance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "compliance_check" in data
        assert "export_permitted" in data
    
    def test_gdpr_user_deletion_compliance(self, test_client, auth_headers):
        """Test GDPR compliance with user deletion."""
        response = test_client.post(
            "/gdpr/deletion-compliance-check",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deletion_permitted" in data
        assert "retention_requirements" in data