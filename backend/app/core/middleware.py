from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from functools import wraps
from typing import Callable, Any


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


class APILimiter:
    """
    API rate limiting functionality
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        
        # Default rate limits by subscription tier
        self.rate_limits = {
            "free": {
                "general_api": 100,  # requests per hour
                "ai_copilot": 0,     # not allowed
                "output_generation": 0  # not allowed
            },
            "premium": {
                "general_api": 1000,  # requests per hour
                "ai_copilot": 50,     # requests per hour
                "output_generation": 20  # requests per day
            }
        }
    
    def check_rate_limit(
        self,
        user_id: str,
        subscription_tier: str,
        endpoint_type: str = "general_api",
        time_window: int = 3600  # 1 hour in seconds
    ):
        """
        Check if user has exceeded rate limit
        """
        if not self.redis:
            return True  # No rate limiting if Redis not available
        
        limit = self.rate_limits.get(subscription_tier, {}).get(endpoint_type, 0)
        
        if limit == 0:
            raise PremiumAccessError(f"Premium subscription required for {endpoint_type}")
        
        key = f"rate_limit:{user_id}:{endpoint_type}:{time_window}"
        current_count = self.redis.get(key)
        
        if current_count is None:
            # First request in this time window
            self.redis.setex(key, time_window, 1)
            return True
        
        current_count = int(current_count)
        if current_count >= limit:
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {limit} requests per {time_window} seconds",
                retry_after=self.redis.ttl(key)
            )
        
        # Increment counter
        self.redis.incr(key)
        return True
    
    def create_rate_limit_dependency(self, endpoint_type: str = "general_api"):
        """
        Create a FastAPI dependency for rate limiting
        """
        async def _rate_limit_check(
            request: Request,
            current_user: User = Depends(get_current_user)
        ):
            self.check_rate_limit(
                user_id=str(current_user.id),
                subscription_tier=current_user.subscription_tier,
                endpoint_type=endpoint_type
            )
            return True
        
        return _rate_limit_check


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