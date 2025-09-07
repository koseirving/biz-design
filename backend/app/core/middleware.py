from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from functools import wraps
from typing import Callable, Any, Dict, Optional
import redis
import json
import time
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


class PremiumAccessError(HTTPException):
    def __init__(self, message: str = "Premium subscription required"):
        super().__init__(status_code=403, detail=message)


class RateLimitError(HTTPException):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(status_code=429, detail=message)
        if retry_after:
            self.headers = {"Retry-After": str(retry_after)}


def require_premium(func: Callable) -> Callable:
    """
    Decorator to require premium subscription for endpoints
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the current_user parameter
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break
        
        if 'current_user' in kwargs:
            current_user = kwargs['current_user']
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        if current_user.subscription_tier != "premium":
            raise PremiumAccessError("Premium subscription required to access this feature")
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_subscription_tier(required_tier: str):
    """
    Decorator to require specific subscription tier
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the current_user parameter
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Define tier hierarchy
            tier_levels = {
                "free": 0,
                "premium": 1
            }
            
            user_level = tier_levels.get(current_user.subscription_tier, 0)
            required_level = tier_levels.get(required_tier, 1)
            
            if user_level < required_level:
                raise PremiumAccessError(f"{required_tier.title()} subscription required")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_framework_access(framework_service):
    """
    Dependency to check if user has access to a specific framework
    """
    async def _check_access(
        framework_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        framework = framework_service.get_framework_by_id(db, framework_id)
        
        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")
        
        if framework.is_premium and current_user.subscription_tier != "premium":
            raise PremiumAccessError("Premium subscription required for this framework")
        
        return framework
    
    return _check_access


class RateLimitStrategy:
    """Rate limiting strategies"""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"


class APILimiter:
    """
    Advanced API rate limiting functionality with multiple strategies
    """
    
    def __init__(self, redis_client=None, strategy=RateLimitStrategy.SLIDING_WINDOW):
        self.redis = redis_client
        self.strategy = strategy
        
        # Default rate limits by subscription tier and endpoint type
        self.rate_limits = {
            "free": {
                "general_api": {"requests": 100, "window": 3600},    # 100 requests per hour
                "ai_copilot": {"requests": 0, "window": 3600},       # not allowed
                "output_generation": {"requests": 0, "window": 86400}, # not allowed
                "data_export": {"requests": 2, "window": 86400},     # 2 exports per day
                "auth": {"requests": 10, "window": 900}              # 10 auth attempts per 15 min
            },
            "premium": {
                "general_api": {"requests": 1000, "window": 3600},   # 1000 requests per hour
                "ai_copilot": {"requests": 50, "window": 3600},      # 50 AI requests per hour
                "output_generation": {"requests": 20, "window": 86400}, # 20 outputs per day
                "data_export": {"requests": 10, "window": 86400},    # 10 exports per day
                "auth": {"requests": 20, "window": 900}              # 20 auth attempts per 15 min
            }
        }
        
        # Rate limit headers configuration
        self.headers_config = {
            "include_headers": True,
            "header_prefix": "X-RateLimit"
        }
    
    def check_rate_limit(
        self,
        user_id: str,
        subscription_tier: str,
        endpoint_type: str = "general_api",
        request_weight: int = 1
    ) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limit and return limit info
        """
        if not self.redis:
            logger.warning("Redis not available, rate limiting disabled")
            return {"allowed": True, "reason": "redis_unavailable"}
        
        limit_config = self.rate_limits.get(subscription_tier, {}).get(endpoint_type)
        
        if not limit_config:
            raise HTTPException(
                status_code=403,
                detail=f"No rate limit configuration for {subscription_tier}/{endpoint_type}"
            )
        
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]
        
        # Check if endpoint is disabled for this tier
        if max_requests == 0:
            raise PremiumAccessError(f"Premium subscription required for {endpoint_type}")
        
        # Use appropriate strategy
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(user_id, endpoint_type, max_requests, window_seconds, request_weight)
        elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(user_id, endpoint_type, max_requests, window_seconds, request_weight)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(user_id, endpoint_type, max_requests, window_seconds, request_weight)
        else:
            raise ValueError(f"Unknown rate limit strategy: {self.strategy}")
    
    def _check_sliding_window(
        self, 
        user_id: str, 
        endpoint_type: str, 
        max_requests: int, 
        window_seconds: int,
        request_weight: int
    ) -> Dict[str, Any]:
        """Sliding window rate limiting implementation"""
        
        now = time.time()
        key = f"rate_limit:sliding:{user_id}:{endpoint_type}"
        
        # Clean old entries and count current requests
        pipe = self.redis.pipeline()
        
        # Remove entries older than window
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        request_id = f"{now}:{request_weight}"
        pipe.zadd(key, {request_id: now})
        
        # Set expiration
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        current_count = results[1]
        
        # Check if limit exceeded (before adding current request)
        if current_count + request_weight > max_requests:
            # Remove the request we just added since it's rejected
            self.redis.zrem(key, request_id)
            
            # Calculate retry after time
            oldest_requests = self.redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest_requests[0][1] + window_seconds - now) if oldest_requests else window_seconds
            
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds",
                retry_after=retry_after
            )
        
        remaining = max_requests - (current_count + request_weight)
        reset_time = now + window_seconds
        
        return {
            "allowed": True,
            "limit": max_requests,
            "remaining": max(0, remaining),
            "reset_time": int(reset_time),
            "window_seconds": window_seconds
        }
    
    def _check_fixed_window(
        self, 
        user_id: str, 
        endpoint_type: str, 
        max_requests: int, 
        window_seconds: int,
        request_weight: int
    ) -> Dict[str, Any]:
        """Fixed window rate limiting implementation"""
        
        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        key = f"rate_limit:fixed:{user_id}:{endpoint_type}:{window_start}"
        
        current_count = self.redis.get(key)
        current_count = int(current_count) if current_count else 0
        
        if current_count + request_weight > max_requests:
            retry_after = int(window_start + window_seconds - now)
            
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds",
                retry_after=retry_after
            )
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incrby(key, request_weight)
        pipe.expire(key, window_seconds)
        pipe.execute()
        
        remaining = max_requests - (current_count + request_weight)
        reset_time = window_start + window_seconds
        
        return {
            "allowed": True,
            "limit": max_requests,
            "remaining": max(0, remaining),
            "reset_time": int(reset_time),
            "window_seconds": window_seconds
        }
    
    def _check_token_bucket(
        self, 
        user_id: str, 
        endpoint_type: str, 
        max_requests: int, 
        window_seconds: int,
        request_weight: int
    ) -> Dict[str, Any]:
        """Token bucket rate limiting implementation"""
        
        now = time.time()
        key = f"rate_limit:bucket:{user_id}:{endpoint_type}"
        
        # Get current bucket state
        bucket_data = self.redis.hgetall(key)
        
        if bucket_data:
            tokens = float(bucket_data.get(b'tokens', max_requests))
            last_refill = float(bucket_data.get(b'last_refill', now))
        else:
            tokens = max_requests
            last_refill = now
        
        # Calculate refill rate (tokens per second)
        refill_rate = max_requests / window_seconds
        
        # Add tokens based on elapsed time
        elapsed = now - last_refill
        new_tokens = min(max_requests, tokens + (elapsed * refill_rate))
        
        # Check if enough tokens available
        if new_tokens < request_weight:
            # Calculate retry after time
            tokens_needed = request_weight - new_tokens
            retry_after = int(tokens_needed / refill_rate)
            
            raise RateLimitError(
                f"Rate limit exceeded. Token bucket exhausted.",
                retry_after=retry_after
            )
        
        # Consume tokens
        remaining_tokens = new_tokens - request_weight
        
        # Update bucket state
        pipe = self.redis.pipeline()
        pipe.hset(key, mapping={
            'tokens': remaining_tokens,
            'last_refill': now
        })
        pipe.expire(key, window_seconds * 2)  # Keep bucket state longer
        pipe.execute()
        
        return {
            "allowed": True,
            "limit": max_requests,
            "remaining": int(remaining_tokens),
            "reset_time": int(now + (max_requests - remaining_tokens) / refill_rate),
            "window_seconds": window_seconds
        }
    
    def get_rate_limit_info(
        self,
        user_id: str,
        subscription_tier: str,
        endpoint_type: str = "general_api"
    ) -> Dict[str, Any]:
        """Get current rate limit status without consuming quota"""
        
        if not self.redis:
            return {"error": "Redis not available"}
        
        limit_config = self.rate_limits.get(subscription_tier, {}).get(endpoint_type)
        if not limit_config:
            return {"error": "No rate limit configuration"}
        
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]
        now = time.time()
        
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            key = f"rate_limit:sliding:{user_id}:{endpoint_type}"
            
            # Clean old entries and count current
            self.redis.zremrangebyscore(key, 0, now - window_seconds)
            current_count = self.redis.zcard(key)
            
            return {
                "limit": max_requests,
                "remaining": max(0, max_requests - current_count),
                "reset_time": int(now + window_seconds),
                "window_seconds": window_seconds
            }
            
        elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
            window_start = int(now // window_seconds) * window_seconds
            key = f"rate_limit:fixed:{user_id}:{endpoint_type}:{window_start}"
            
            current_count = self.redis.get(key)
            current_count = int(current_count) if current_count else 0
            
            return {
                "limit": max_requests,
                "remaining": max(0, max_requests - current_count),
                "reset_time": int(window_start + window_seconds),
                "window_seconds": window_seconds
            }
            
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            key = f"rate_limit:bucket:{user_id}:{endpoint_type}"
            bucket_data = self.redis.hgetall(key)
            
            if bucket_data:
                tokens = float(bucket_data.get(b'tokens', max_requests))
                last_refill = float(bucket_data.get(b'last_refill', now))
                
                # Calculate current tokens
                refill_rate = max_requests / window_seconds
                elapsed = now - last_refill
                current_tokens = min(max_requests, tokens + (elapsed * refill_rate))
            else:
                current_tokens = max_requests
            
            return {
                "limit": max_requests,
                "remaining": int(current_tokens),
                "reset_time": int(now + (max_requests - current_tokens) / (max_requests / window_seconds)),
                "window_seconds": window_seconds
            }
    
    def reset_rate_limit(self, user_id: str, endpoint_type: str) -> bool:
        """Reset rate limit for a user/endpoint (admin function)"""
        
        if not self.redis:
            return False
        
        patterns = [
            f"rate_limit:sliding:{user_id}:{endpoint_type}",
            f"rate_limit:fixed:{user_id}:{endpoint_type}:*",
            f"rate_limit:bucket:{user_id}:{endpoint_type}"
        ]
        
        deleted = 0
        for pattern in patterns:
            if '*' in pattern:
                keys = self.redis.keys(pattern)
                if keys:
                    deleted += self.redis.delete(*keys)
            else:
                deleted += self.redis.delete(pattern)
        
        logger.info(f"Reset rate limit for {user_id}:{endpoint_type}, deleted {deleted} keys")
        return deleted > 0
    
    def create_rate_limit_dependency(
        self, 
        endpoint_type: str = "general_api", 
        request_weight: int = 1,
        include_headers: bool = True
    ):
        """
        Create a FastAPI dependency for rate limiting with response headers
        """
        async def _rate_limit_check(
            request: Request,
            current_user: User = Depends(get_current_user)
        ):
            try:
                rate_limit_info = self.check_rate_limit(
                    user_id=str(current_user.id),
                    subscription_tier=current_user.subscription_tier,
                    endpoint_type=endpoint_type,
                    request_weight=request_weight
                )
                
                # Add rate limit info to request state for response headers
                if include_headers and self.headers_config["include_headers"]:
                    request.state.rate_limit_info = rate_limit_info
                
                return True
                
            except (RateLimitError, PremiumAccessError) as e:
                # Add rate limit headers even for errors
                if include_headers and self.headers_config["include_headers"]:
                    limit_info = self.get_rate_limit_info(
                        user_id=str(current_user.id),
                        subscription_tier=current_user.subscription_tier,
                        endpoint_type=endpoint_type
                    )
                    request.state.rate_limit_info = limit_info
                
                raise e
        
        return _rate_limit_check
    
    def add_rate_limit_headers(self, response, rate_limit_info: Dict[str, Any]) -> None:
        """Add rate limit headers to response"""
        
        if not self.headers_config["include_headers"]:
            return
        
        prefix = self.headers_config["header_prefix"]
        
        response.headers[f"{prefix}-Limit"] = str(rate_limit_info.get("limit", "unknown"))
        response.headers[f"{prefix}-Remaining"] = str(rate_limit_info.get("remaining", "unknown"))
        response.headers[f"{prefix}-Reset"] = str(rate_limit_info.get("reset_time", "unknown"))
        response.headers[f"{prefix}-Window"] = str(rate_limit_info.get("window_seconds", "unknown"))
        
        # Add additional headers for debugging
        response.headers[f"{prefix}-Strategy"] = self.strategy
        
        if "error" in rate_limit_info:
            response.headers[f"{prefix}-Error"] = rate_limit_info["error"]


# Global rate limiter instance (will be initialized with Redis in main.py)
rate_limiter = APILimiter()


# Pre-configured dependencies for common rate limits
def require_general_api_limit():
    return rate_limiter.create_rate_limit_dependency("general_api")


def require_ai_copilot_limit():
    return rate_limiter.create_rate_limit_dependency("ai_copilot")


def require_output_generation_limit():
    return rate_limiter.create_rate_limit_dependency("output_generation")


# Utility functions for subscription checks
def is_premium_user(user: User) -> bool:
    """Check if user has premium subscription"""
    return user.subscription_tier == "premium"


def can_access_premium_features(user: User) -> bool:
    """Check if user can access premium features"""
    return user.subscription_tier == "premium"


def get_user_limits(subscription_tier: str) -> dict:
    """Get rate limits for user's subscription tier"""
    return rate_limiter.rate_limits.get(subscription_tier, {})


# Middleware for adding subscription info to requests
class SubscriptionMiddleware:
    """
    Middleware to add subscription information to request state
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Add subscription context if user is authenticated
            try:
                # This would require extracting user info from JWT token
                # Implementation depends on your auth setup
                pass
            except Exception:
                pass
        
        await self.app(scope, receive, send)