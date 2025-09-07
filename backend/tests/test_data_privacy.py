import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os

from app.services.data_export_service import DataExportService
from app.services.account_deletion_service import AccountDeletionService


class TestDataExport:
    """Test data export functionality."""
    
    def test_request_data_export_success(self, test_client, auth_headers, sample_export_request):
        """Test successful data export request."""
        response = test_client.post(
            "/users/data-export",
            json=sample_export_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Data export created successfully"
        assert "export_info" in data
        assert "export_id" in data["export_info"]
    
    def test_request_data_export_invalid_format(self, test_client, auth_headers):
        """Test data export with invalid format."""
        invalid_request = {
            "formats": ["invalid_format"]
        }
        
        response = test_client.post(
            "/users/data-export",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid export formats" in response.json()["detail"]
    
    def test_get_export_status(self, test_client, auth_headers):
        """Test getting export status."""
        # First create an export
        export_response = test_client.post(
            "/users/data-export",
            json={"formats": ["json"]},
            headers=auth_headers
        )
        export_id = export_response.json()["export_info"]["export_id"]
        
        # Then check status
        response = test_client.get(
            f"/users/export-status/{export_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "export_id" in data
    
    @patch('os.path.exists')
    def test_download_export_file_success(self, mock_exists, test_client):
        """Test successful file download."""
        mock_exists.return_value = True
        
        with patch('fastapi.responses.FileResponse') as mock_file_response:
            mock_file_response.return_value = Mock()
            
            response = test_client.get("/users/download/test_export.json")
            
            assert response.status_code == 200
            mock_file_response.assert_called_once()
    
    @patch('os.path.exists')
    def test_download_export_file_not_found(self, mock_exists, test_client):
        """Test download of non-existent file."""
        mock_exists.return_value = False
        
        response = test_client.get("/users/download/nonexistent.json")
        
        assert response.status_code == 404
        assert "Export file not found" in response.json()["detail"]
    
    @patch('app.services.data_export_service.DataExportService')
    def test_data_export_service_integration(self, mock_service_class):
        """Test data export service integration."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock export creation
        mock_service.create_export_request.return_value = {
            "export_id": "test-export-id",
            "status": "processing",
            "formats": ["json", "csv"]
        }
        
        service = DataExportService()
        result = service.create_export_request(
            db=Mock(),
            user_id="test-user-id",
            formats=["json", "csv"]
        )
        
        assert result["export_id"] == "test-export-id"
        assert result["formats"] == ["json", "csv"]


class TestAccountDeletion:
    """Test account deletion functionality."""
    
    def test_get_deletion_impact(self, test_client, auth_headers):
        """Test getting deletion impact assessment."""
        response = test_client.get(
            "/users/deletion-impact",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "impact_assessment" in data
        assert "warning" in data
        assert "cancellation_period" in data
    
    def test_request_account_deletion_success(self, test_client, auth_headers, sample_deletion_request):
        """Test successful account deletion request."""
        response = test_client.post(
            "/users/request-deletion",
            json=sample_deletion_request,
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Account deletion request processed successfully"
        assert "deletion_info" in data
        assert "next_steps" in data
        assert "cancellation" in data
    
    def test_request_account_deletion_invalid_confirmation(self, test_client, auth_headers):
        """Test account deletion without proper confirmation."""
        invalid_request = {
            "reason": "user_request",
            "confirm_deletion": False,
            "understand_consequences": True
        }
        
        response = test_client.post(
            "/users/request-deletion",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Account deletion must be confirmed" in response.json()["detail"]
    
    def test_request_account_deletion_no_understanding(self, test_client, auth_headers):
        """Test account deletion without understanding consequences."""
        invalid_request = {
            "reason": "user_request",
            "confirm_deletion": True,
            "understand_consequences": False
        }
        
        response = test_client.post(
            "/users/request-deletion",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "User must understand deletion consequences" in response.json()["detail"]
    
    def test_cancel_account_deletion(self, test_client, auth_headers, sample_deletion_request):
        """Test canceling account deletion."""
        # First request deletion
        deletion_response = test_client.post(
            "/users/request-deletion",
            json=sample_deletion_request,
            headers=auth_headers
        )
        deletion_id = deletion_response.json()["deletion_info"]["deletion_id"]
        
        # Then cancel it
        response = test_client.post(
            f"/users/cancel-deletion/{deletion_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Account deletion request cancelled successfully"
        assert data["account_status"] == "reactivated"
    
    def test_get_deletion_status(self, test_client, auth_headers):
        """Test getting deletion status."""
        response = test_client.get(
            "/users/deletion-status",
            headers=auth_headers
        )
        
        # This might return 404 if no deletion is pending
        assert response.status_code in [200, 404]
    
    @patch('app.services.account_deletion_service.AccountDeletionService')
    def test_account_deletion_service_integration(self, mock_service_class, db_session):
        """Test account deletion service integration."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock deletion initiation
        mock_service.initiate_deletion_request.return_value = {
            "deletion_id": "test-deletion-id",
            "timeline": {
                "soft_delete": "2024-01-01T12:00:00Z",
                "anonymization": "2024-01-02T12:00:00Z",
                "hard_delete": "2024-01-31T12:00:00Z"
            },
            "cancellable_until": "2024-01-31T12:00:00Z"
        }
        
        service = AccountDeletionService(db_session)
        result = service.initiate_deletion_request(
            user_id="test-user-id",
            reason="user_request"
        )
        
        assert result["deletion_id"] == "test-deletion-id"
        assert "timeline" in result


class TestDataPrivacyIntegration:
    """Test data privacy feature integration."""
    
    def test_export_audit_logging(self, test_client, auth_headers):
        """Test that export requests are properly audited."""
        with patch('app.services.audit_log_service.audit_data_access') as mock_audit:
            response = test_client.post(
                "/users/data-export",
                json={"formats": ["json"]},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            # Verify audit logging was called
            mock_audit.assert_called()
    
    def test_deletion_audit_logging(self, test_client, auth_headers, sample_deletion_request):
        """Test that deletion requests are properly audited."""
        with patch('app.services.audit_log_service.audit_logger') as mock_audit:
            response = test_client.post(
                "/users/request-deletion",
                json=sample_deletion_request,
                headers=auth_headers
            )
            
            assert response.status_code == 202
            # Verify audit logging was called
            mock_audit.log_event.assert_called()
    
    def test_gdpr_export_compliance(self, test_client, auth_headers):
        """Test GDPR compliance of data export."""
        # This should include consent checks, data minimization, etc.
        response = test_client.post(
            "/users/data-export",
            json={"formats": ["json", "csv"]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify GDPR compliance indicators
        export_info = data["export_info"]
        assert "gdpr_compliant" in export_info
        assert export_info["gdpr_compliant"] is True
    
    def test_staged_deletion_process(self, test_client, auth_headers, sample_deletion_request):
        """Test the staged deletion process compliance."""
        response = test_client.post(
            "/users/request-deletion",
            json=sample_deletion_request,
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify staged process is described
        next_steps = data["next_steps"]
        assert "immediate" in next_steps
        assert "24_hours" in next_steps
        assert "30_days" in next_steps
        
        # Verify cancellation period
        cancellation = data["cancellation"]
        assert "possible_until" in cancellation
        assert "instructions" in cancellation


class TestDataPrivacyErrors:
    """Test error handling in data privacy features."""
    
    def test_export_service_failure(self, test_client, auth_headers):
        """Test handling of export service failures."""
        with patch('app.services.data_export_service.DataExportService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.create_export_request.side_effect = Exception("Export service error")
            
            response = test_client.post(
                "/users/data-export",
                json={"formats": ["json"]},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            assert "Failed to export data" in response.json()["detail"]
    
    def test_deletion_service_failure(self, test_client, auth_headers, sample_deletion_request):
        """Test handling of deletion service failures."""
        with patch('app.services.account_deletion_service.AccountDeletionService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.initiate_deletion_request.side_effect = Exception("Deletion service error")
            
            response = test_client.post(
                "/users/request-deletion",
                json=sample_deletion_request,
                headers=auth_headers
            )
            
            assert response.status_code == 500
            assert "Failed to process deletion request" in response.json()["detail"]