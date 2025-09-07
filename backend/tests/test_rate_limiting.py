import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import redis
import time
from datetime import datetime, timedelta

from app.core.middleware import APILimiter
from app.services.audit_log_service import AuditEventType


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_status(self, test_client, auth_headers):
        """Test getting rate limit status."""
        response = test_client.get(
            "/admin/rate-limits/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "rate_limits" in data
        assert "current_usage" in data
        assert "reset_times" in data
    
    def test_endpoint_rate_limit_status(self, test_client, auth_headers):
        """Test getting endpoint-specific rate limit status."""
        response = test_client.get(
            "/admin/rate-limits/endpoint/ai_interaction",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "endpoint_type" in data
        assert "current_usage" in data
        assert "limit" in data
        assert "reset_time" in data
    
    def test_rate_limit_configuration(self, test_client, premium_auth_headers):
        """Test getting rate limit configuration."""
        response = test_client.get(
            "/admin/rate-limits/configuration",
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "rate_limits" in data
        assert "strategies" in data
        assert "redis_config" in data
    
    def test_rate_limit_configuration_unauthorized(self, test_client, auth_headers):
        """Test rate limit configuration access without admin rights."""
        response = test_client.get(
            "/admin/rate-limits/configuration",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_update_rate_limits_success(self, test_client, premium_auth_headers):
        """Test updating rate limits."""
        update_data = {
            "endpoint_type": "ai_interaction",
            "free_tier": {
                "requests_per_minute": 5,
                "requests_per_hour": 50
            },
            "premium_tier": {
                "requests_per_minute": 20,
                "requests_per_hour": 200
            }
        }
        
        response = test_client.put(
            "/admin/rate-limits/configuration",
            json=update_data,
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Rate limits updated successfully"
    
    def test_test_rate_limit(self, test_client, auth_headers):
        """Test rate limit testing endpoint."""
        test_data = {
            "endpoint_type": "ai_interaction",
            "num_requests": 3
        }
        
        response = test_client.post(
            "/admin/rate-limits/test",
            json=test_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "test_results" in data
        assert "requests_made" in data["test_results"]
        assert "rate_limited_after" in data["test_results"]
    
    def test_rate_limit_analytics(self, test_client, premium_auth_headers):
        """Test rate limit analytics."""
        response = test_client.get(
            "/admin/rate-limits/analytics?period_hours=24",
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "total_requests" in data["analytics"]
        assert "rate_limited_requests" in data["analytics"]
        assert "top_endpoints" in data["analytics"]
    
    def test_reset_user_rate_limit(self, test_client, premium_auth_headers):
        """Test resetting user rate limit."""
        reset_data = {
            "user_id": "test-user-id",
            "endpoint_type": "ai_interaction"
        }
        
        response = test_client.post(
            "/admin/rate-limits/reset",
            json=reset_data,
            headers=premium_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Rate limit reset successfully"
    
    def test_rate_limit_health_check(self, test_client):
        """Test rate limit system health check."""
        response = test_client.get("/admin/rate-limits/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "redis_connected" in data
        assert "strategies_active" in data


class TestAPILimiter:
    """Test APILimiter class directly."""
    
    @pytest.fixture
    def api_limiter(self, fake_redis):
        """Create APILimiter with fake Redis."""
        return APILimiter(redis=fake_redis)
    
    def test_sliding_window_rate_limiting(self, api_limiter, fake_redis):
        """Test sliding window rate limiting."""
        user_id = "test-user"
        endpoint_type = "test_endpoint"
        max_requests = 5
        window_seconds = 60
        
        # Make requests within limit
        for i in range(max_requests):
            result = api_limiter._check_sliding_window(
                user_id, endpoint_type, max_requests, window_seconds
            )
            assert result["allowed"] is True
            assert result["requests_made"] == i + 1
        
        # Exceed limit
        result = api_limiter._check_sliding_window(
            user_id, endpoint_type, max_requests, window_seconds
        )
        assert result["allowed"] is False
        assert result["requests_made"] == max_requests + 1
    
    def test_fixed_window_rate_limiting(self, api_limiter, fake_redis):
        """Test fixed window rate limiting."""
        user_id = "test-user"
        endpoint_type = "test_endpoint"
        max_requests = 5
        window_seconds = 60
        
        # Make requests within limit
        for i in range(max_requests):
            result = api_limiter._check_fixed_window(
                user_id, endpoint_type, max_requests, window_seconds
            )
            assert result["allowed"] is True
        
        # Exceed limit
        result = api_limiter._check_fixed_window(
            user_id, endpoint_type, max_requests, window_seconds
        )
        assert result["allowed"] is False
    
    def test_token_bucket_rate_limiting(self, api_limiter, fake_redis):
        """Test token bucket rate limiting."""
        user_id = "test-user"
        endpoint_type = "test_endpoint"
        bucket_size = 5
        refill_rate = 1  # 1 token per second
        
        # Make requests within bucket capacity
        for i in range(bucket_size):
            result = api_limiter._check_token_bucket(
                user_id, endpoint_type, bucket_size, refill_rate
            )
            assert result["allowed"] is True
        
        # Exceed bucket capacity
        result = api_limiter._check_token_bucket(
            user_id, endpoint_type, bucket_size, refill_rate
        )
        assert result["allowed"] is False
    
    def test_check_rate_limit_free_tier(self, api_limiter):
        """Test rate limiting for free tier users."""
        result = api_limiter.check_rate_limit(
            user_id="free-user",
            endpoint_type="ai_interaction",
            subscription_tier="free"
        )
        
        assert "allowed" in result
        assert "rate_limit_info" in result
        assert result["rate_limit_info"]["tier"] == "free"
    
    def test_check_rate_limit_premium_tier(self, api_limiter):
        """Test rate limiting for premium tier users."""
        result = api_limiter.check_rate_limit(
            user_id="premium-user",
            endpoint_type="ai_interaction",
            subscription_tier="premium"
        )
        
        assert "allowed" in result
        assert "rate_limit_info" in result
        assert result["rate_limit_info"]["tier"] == "premium"
    
    def test_get_rate_limit_info(self, api_limiter):
        """Test getting rate limit information."""
        info = api_limiter.get_rate_limit_info(
            user_id="test-user",
            endpoint_type="ai_interaction"
        )
        
        assert "current_usage" in info
        assert "limits" in info
        assert "reset_times" in info
    
    def test_reset_rate_limit(self, api_limiter):
        """Test resetting rate limits."""
        # First use some quota
        api_limiter.check_rate_limit(
            user_id="test-user",
            endpoint_type="ai_interaction",
            subscription_tier="free"
        )
        
        # Reset the limit
        result = api_limiter.reset_rate_limit("test-user", "ai_interaction")
        assert result is True
        
        # Verify reset worked
        info = api_limiter.get_rate_limit_info("test-user", "ai_interaction")
        assert info["current_usage"]["sliding_window"] == 0
    
    def test_rate_limit_headers(self, api_limiter):
        """Test rate limit header generation."""
        from fastapi import Response
        
        response = Response()
        rate_limit_info = {
            "current_usage": {"sliding_window": 5},
            "limits": {"sliding_window": 10},
            "reset_times": {"sliding_window": time.time() + 60}
        }
        
        api_limiter.add_rate_limit_headers(response, rate_limit_info)
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestRateLimitingIntegration:
    """Test rate limiting integration with other systems."""
    
    def test_rate_limit_audit_logging(self, test_client, auth_headers):
        """Test that rate limit events are audited."""
        with patch('app.services.audit_log_service.audit_logger') as mock_audit:
            # Make requests to trigger rate limiting
            for _ in range(10):  # Assume this exceeds free tier limits
                response = test_client.post(
                    "/ai/interact",
                    json={"message": "test"},
                    headers=auth_headers
                )
                
                if response.status_code == 429:
                    break
            
            # Verify audit logging was called for rate limit events
            mock_audit.log_event.assert_called()
            
            # Check if any call was for rate limiting
            calls = mock_audit.log_event.call_args_list
            rate_limit_calls = [
                call for call in calls 
                if len(call.kwargs) > 0 and 
                call.kwargs.get('event_type') == AuditEventType.RATE_LIMIT_EXCEEDED
            ]
            assert len(rate_limit_calls) > 0
    
    def test_rate_limit_with_authentication(self, test_client):
        """Test rate limiting behavior with different authentication states."""
        # Test without authentication (should still be rate limited)
        response = test_client.get("/admin/rate-limits/health")
        assert response.status_code == 200  # Health endpoint should be accessible
        
        # Test with invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get(
            "/admin/rate-limits/status",
            headers=invalid_headers
        )
        assert response.status_code == 401  # Should fail authentication first
    
    @patch('app.core.middleware.redis.Redis')
    def test_rate_limit_redis_failure_handling(self, mock_redis, test_client, auth_headers):
        """Test rate limiting behavior when Redis is unavailable."""
        # Mock Redis connection failure
        mock_redis.side_effect = redis.ConnectionError("Redis unavailable")
        
        response = test_client.get(
            "/admin/rate-limits/status",
            headers=auth_headers
        )
        
        # Should still respond but might have degraded functionality
        assert response.status_code in [200, 503]  # Either works or service unavailable
    
    def test_concurrent_rate_limiting(self, api_limiter, fake_redis):
        """Test rate limiting under concurrent access."""
        import threading
        import time
        
        user_id = "concurrent-user"
        endpoint_type = "test_endpoint"
        results = []
        
        def make_request():
            result = api_limiter.check_rate_limit(
                user_id=user_id,
                endpoint_type=endpoint_type,
                subscription_tier="free"
            )
            results.append(result["allowed"])
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have some allowed and some denied requests
        allowed_count = sum(results)
        assert 0 < allowed_count < len(results)  # Some should be allowed, some denied


class TestRateLimitingEdgeCases:
    """Test edge cases in rate limiting."""
    
    def test_rate_limit_with_zero_limits(self, api_limiter):
        """Test rate limiting with zero request limits."""
        result = api_limiter.check_rate_limit(
            user_id="zero-limit-user",
            endpoint_type="blocked_endpoint",  # Assume this has 0 limit
            subscription_tier="free"
        )
        
        # Should be immediately denied
        assert result["allowed"] is False
    
    def test_rate_limit_time_boundary(self, api_limiter, fake_redis):
        """Test rate limiting at time window boundaries."""
        user_id = "boundary-user"
        endpoint_type = "test_endpoint"
        
        # Mock time to be at window boundary
        with patch('time.time') as mock_time:
            # Start of window
            mock_time.return_value = 1000.0
            
            # Make requests
            for _ in range(5):
                api_limiter._check_fixed_window(user_id, endpoint_type, 5, 60)
            
            # Move to end of window
            mock_time.return_value = 1059.0  # 59 seconds later
            result = api_limiter._check_fixed_window(user_id, endpoint_type, 5, 60)
            assert result["allowed"] is False  # Still in same window
            
            # Move to new window
            mock_time.return_value = 1061.0  # 61 seconds later
            result = api_limiter._check_fixed_window(user_id, endpoint_type, 5, 60)
            assert result["allowed"] is True  # New window, reset counter
    
    def test_rate_limit_negative_values(self, api_limiter):
        """Test rate limiting with negative or invalid values."""
        with pytest.raises(ValueError):
            api_limiter._check_sliding_window(
                "user", "endpoint", -1, 60  # Negative max_requests
            )
        
        with pytest.raises(ValueError):
            api_limiter._check_sliding_window(
                "user", "endpoint", 10, -60  # Negative window_seconds
            )