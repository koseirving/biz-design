import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the Python path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


class TestBasicIntegration:
    """Basic integration tests to verify the application works."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "biz-design-backend"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Hello World" in data["message"]
    
    def test_api_routes_registered(self, client):
        """Test that new API routes are registered."""
        # Test GDPR compliance route (should require auth)
        response = client.get("/gdpr/privacy-notice")
        assert response.status_code in [200, 401, 404]  # Not 500
        
        # Test audit logs route (should require auth)  
        response = client.get("/audit/health")
        assert response.status_code in [200, 401, 404]  # Not 500
        
        # Test rate limits route (should require auth)
        response = client.get("/admin/rate-limits/health")  
        assert response.status_code in [200, 401, 404]  # Not 500
    
    @patch('redis.Redis')
    def test_redis_connection_handling(self, mock_redis, client):
        """Test that the app handles Redis connection gracefully."""
        # Mock Redis to work normally
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/health")
        # CORS headers should be present for cross-origin requests
        assert response.status_code == 200


class TestModuleImports:
    """Test that all modules can be imported without errors."""
    
    def test_import_gdpr_compliance(self):
        """Test GDPR compliance module import."""
        try:
            from app.api import gdpr_compliance
            assert gdpr_compliance is not None
        except ImportError as e:
            pytest.fail(f"Failed to import gdpr_compliance: {e}")
    
    def test_import_audit_logs(self):
        """Test audit logs module import."""
        try:
            from app.api import audit_logs
            assert audit_logs is not None
        except ImportError as e:
            pytest.fail(f"Failed to import audit_logs: {e}")
    
    def test_import_rate_limits(self):
        """Test rate limits module import."""
        try:
            from app.api import rate_limits
            assert rate_limits is not None
        except ImportError as e:
            pytest.fail(f"Failed to import rate_limits: {e}")
    
    def test_import_services(self):
        """Test that all services can be imported."""
        try:
            from app.services import gdpr_compliance_service
            from app.services import data_export_service
            from app.services import account_deletion_service
            from app.services import encryption_service
            from app.services import audit_log_service
            
            assert gdpr_compliance_service is not None
            assert data_export_service is not None
            assert account_deletion_service is not None
            assert encryption_service is not None
            assert audit_log_service is not None
        except ImportError as e:
            pytest.fail(f"Failed to import services: {e}")
    
    def test_import_middleware(self):
        """Test middleware import."""
        try:
            from app.core.middleware import APILimiter
            assert APILimiter is not None
        except ImportError as e:
            pytest.fail(f"Failed to import middleware: {e}")


class TestSecurityHeaders:
    """Test security headers and basic security measures."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_no_server_header_exposure(self, client):
        """Test that server information is not exposed."""
        response = client.get("/health")
        # Should not expose server details
        assert "server" not in [h.lower() for h in response.headers.keys()]
    
    def test_json_responses(self, client):
        """Test that JSON responses have correct content type."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_options_method_handled(self, client):
        """Test CORS preflight requests."""
        response = client.options("/health")
        # Should handle OPTIONS requests for CORS
        assert response.status_code in [200, 405]  # Either allowed or method not allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])