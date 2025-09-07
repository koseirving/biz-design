from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.middleware import rate_limiter, RateLimitStrategy
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])


# Request/Response Models
class RateLimitStatus(BaseModel):
    endpoint_type: str
    limit: int
    remaining: int
    reset_time: int
    window_seconds: int
    strategy: str


class RateLimitConfiguration(BaseModel):
    subscription_tier: str
    endpoint_type: str
    requests: int
    window_seconds: int


class RateLimitUsage(BaseModel):
    user_id: str
    subscription_tier: str
    endpoint_usage: Dict[str, Dict[str, Any]]
    total_requests_today: int
    last_request_at: Optional[str]


# Rate Limit Status Endpoints
@router.get("/status", response_model=Dict[str, Any])
async def get_rate_limit_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get current rate limit status for all endpoint types"""
    
    try:
        user_id = str(current_user.id)
        subscription_tier = current_user.subscription_tier
        
        # Get all configured endpoint types for this subscription tier
        endpoint_types = list(rate_limiter.rate_limits.get(subscription_tier, {}).keys())
        
        status_info = {}
        
        for endpoint_type in endpoint_types:
            limit_info = rate_limiter.get_rate_limit_info(
                user_id=user_id,
                subscription_tier=subscription_tier,
                endpoint_type=endpoint_type
            )
            
            if "error" not in limit_info:
                status_info[endpoint_type] = {
                    **limit_info,
                    "strategy": rate_limiter.strategy
                }
        
        return {
            "user_id": user_id,
            "subscription_tier": subscription_tier,
            "rate_limits": status_info,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )


@router.get("/status/{endpoint_type}", response_model=Dict[str, Any])
async def get_endpoint_rate_limit_status(
    endpoint_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get rate limit status for a specific endpoint type"""
    
    try:
        user_id = str(current_user.id)
        subscription_tier = current_user.subscription_tier
        
        # Validate endpoint type
        if endpoint_type not in rate_limiter.rate_limits.get(subscription_tier, {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Endpoint type '{endpoint_type}' not found for {subscription_tier} tier"
            )
        
        limit_info = rate_limiter.get_rate_limit_info(
            user_id=user_id,
            subscription_tier=subscription_tier,
            endpoint_type=endpoint_type
        )
        
        if "error" in limit_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=limit_info["error"]
            )
        
        return {
            "user_id": user_id,
            "subscription_tier": subscription_tier,
            "endpoint_type": endpoint_type,
            "rate_limit": {
                **limit_info,
                "strategy": rate_limiter.strategy
            },
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit status for {endpoint_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )


# Rate Limit Configuration Endpoints
@router.get("/configuration", response_model=Dict[str, Any])
async def get_rate_limit_configuration(
    current_user: User = Depends(get_current_active_user)
):
    """Get rate limit configuration for current user's subscription tier"""
    
    try:
        subscription_tier = current_user.subscription_tier
        tier_config = rate_limiter.rate_limits.get(subscription_tier, {})
        
        if not tier_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rate limit configuration found for {subscription_tier} tier"
            )
        
        # Format configuration for response
        formatted_config = []
        for endpoint_type, limits in tier_config.items():
            formatted_config.append({
                "endpoint_type": endpoint_type,
                "requests_per_window": limits["requests"],
                "window_seconds": limits["window"],
                "window_description": _format_window_description(limits["window"]),
                "enabled": limits["requests"] > 0
            })
        
        return {
            "subscription_tier": subscription_tier,
            "strategy": rate_limiter.strategy,
            "rate_limit_configuration": formatted_config,
            "headers_included": rate_limiter.headers_config["include_headers"],
            "header_prefix": rate_limiter.headers_config["header_prefix"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit configuration"
        )


@router.get("/usage-summary", response_model=Dict[str, Any])
async def get_usage_summary(
    current_user: User = Depends(get_current_active_user)
):
    """Get usage summary across all endpoints"""
    
    try:
        user_id = str(current_user.id)
        subscription_tier = current_user.subscription_tier
        
        # Get current status for all endpoints
        endpoint_types = list(rate_limiter.rate_limits.get(subscription_tier, {}).keys())
        
        usage_summary = {
            "user_id": user_id,
            "subscription_tier": subscription_tier,
            "total_endpoints": len(endpoint_types),
            "endpoint_usage": {},
            "usage_percentage": {},
            "warnings": []
        }
        
        total_used = 0
        total_available = 0
        
        for endpoint_type in endpoint_types:
            limit_info = rate_limiter.get_rate_limit_info(
                user_id=user_id,
                subscription_tier=subscription_tier,
                endpoint_type=endpoint_type
            )
            
            if "error" not in limit_info:
                limit = limit_info["limit"]
                remaining = limit_info["remaining"]
                used = limit - remaining
                
                usage_percentage = (used / limit * 100) if limit > 0 else 0
                
                usage_summary["endpoint_usage"][endpoint_type] = {
                    "limit": limit,
                    "used": used,
                    "remaining": remaining,
                    "usage_percentage": round(usage_percentage, 2),
                    "window_seconds": limit_info["window_seconds"]
                }
                
                usage_summary["usage_percentage"][endpoint_type] = round(usage_percentage, 2)
                
                # Add warnings for high usage
                if usage_percentage >= 90:
                    usage_summary["warnings"].append({
                        "endpoint_type": endpoint_type,
                        "message": f"High usage: {usage_percentage:.1f}% of limit used",
                        "severity": "critical" if usage_percentage >= 95 else "warning"
                    })
                elif usage_percentage >= 75:
                    usage_summary["warnings"].append({
                        "endpoint_type": endpoint_type,
                        "message": f"Moderate usage: {usage_percentage:.1f}% of limit used", 
                        "severity": "info"
                    })
                
                total_used += used
                total_available += limit
        
        # Calculate overall usage
        usage_summary["overall_usage_percentage"] = (
            round(total_used / total_available * 100, 2) if total_available > 0 else 0
        )
        
        return usage_summary
        
    except Exception as e:
        logger.error(f"Failed to get usage summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage summary"
        )


# Test endpoint for rate limiting
@router.post("/test/{endpoint_type}", response_model=Dict[str, Any])
async def test_rate_limit(
    endpoint_type: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Test rate limiting for a specific endpoint type"""
    
    try:
        user_id = str(current_user.id)
        subscription_tier = current_user.subscription_tier
        
        # Validate endpoint type
        if endpoint_type not in rate_limiter.rate_limits.get(subscription_tier, {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Endpoint type '{endpoint_type}' not found"
            )
        
        # Test the rate limit
        rate_limit_info = rate_limiter.check_rate_limit(
            user_id=user_id,
            subscription_tier=subscription_tier,
            endpoint_type=endpoint_type,
            request_weight=1
        )
        
        return {
            "message": "Rate limit test successful",
            "endpoint_type": endpoint_type,
            "user_id": user_id,
            "subscription_tier": subscription_tier,
            "rate_limit_info": rate_limit_info,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit test failed for {endpoint_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rate limit test failed: {str(e)}"
        )


# Rate limit comparison for subscription tiers
@router.get("/tier-comparison", response_model=Dict[str, Any])
async def get_tier_comparison():
    """Compare rate limits between subscription tiers"""
    
    try:
        comparison = {
            "available_tiers": list(rate_limiter.rate_limits.keys()),
            "strategy": rate_limiter.strategy,
            "comparison_table": {}
        }
        
        # Get all unique endpoint types across tiers
        all_endpoint_types = set()
        for tier_config in rate_limiter.rate_limits.values():
            all_endpoint_types.update(tier_config.keys())
        
        # Build comparison table
        for endpoint_type in sorted(all_endpoint_types):
            comparison["comparison_table"][endpoint_type] = {}
            
            for tier, tier_config in rate_limiter.rate_limits.items():
                if endpoint_type in tier_config:
                    limits = tier_config[endpoint_type]
                    comparison["comparison_table"][endpoint_type][tier] = {
                        "requests_per_window": limits["requests"],
                        "window_seconds": limits["window"],
                        "window_description": _format_window_description(limits["window"]),
                        "enabled": limits["requests"] > 0,
                        "requests_per_hour": _calculate_requests_per_hour(limits)
                    }
                else:
                    comparison["comparison_table"][endpoint_type][tier] = {
                        "requests_per_window": 0,
                        "window_seconds": 0,
                        "window_description": "Not available",
                        "enabled": False,
                        "requests_per_hour": 0
                    }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to get tier comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tier comparison"
        )


# Utility functions
def _format_window_description(window_seconds: int) -> str:
    """Format window duration in human readable format"""
    
    if window_seconds < 60:
        return f"{window_seconds} seconds"
    elif window_seconds < 3600:
        minutes = window_seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    elif window_seconds < 86400:
        hours = window_seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        days = window_seconds // 86400
        return f"{days} day{'s' if days > 1 else ''}"


def _calculate_requests_per_hour(limits: Dict[str, int]) -> float:
    """Calculate equivalent requests per hour"""
    
    requests = limits["requests"]
    window_seconds = limits["window"]
    
    if window_seconds == 0:
        return 0
    
    # Convert to requests per hour
    requests_per_second = requests / window_seconds
    requests_per_hour = requests_per_second * 3600
    
    return round(requests_per_hour, 2)


# Admin endpoints (would require admin role in production)
@router.post("/reset/{user_id}/{endpoint_type}", response_model=Dict[str, Any])
async def reset_user_rate_limit(
    user_id: str,
    endpoint_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Reset rate limit for a specific user and endpoint (admin only)"""
    
    # In production, add admin role check here
    if current_user.subscription_tier != "premium":  # Temporary admin check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        success = rate_limiter.reset_rate_limit(user_id, endpoint_type)
        
        if success:
            return {
                "message": f"Rate limit reset successfully for user {user_id}",
                "user_id": user_id,
                "endpoint_type": endpoint_type,
                "reset_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "message": f"No active rate limits found for user {user_id}",
                "user_id": user_id,
                "endpoint_type": endpoint_type
            }
        
    except Exception as e:
        logger.error(f"Failed to reset rate limit for {user_id}:{endpoint_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limit"
        )


# Health check for rate limiting system
@router.get("/health", response_model=Dict[str, Any])
async def rate_limit_health_check():
    """Health check for rate limiting system"""
    
    try:
        redis_available = rate_limiter.redis is not None
        
        if redis_available:
            try:
                # Test Redis connection
                rate_limiter.redis.ping()
                redis_status = "connected"
            except Exception:
                redis_status = "connection_failed"
                redis_available = False
        else:
            redis_status = "not_configured"
        
        return {
            "status": "healthy" if redis_available else "degraded",
            "redis_available": redis_available,
            "redis_status": redis_status,
            "strategy": rate_limiter.strategy,
            "configured_tiers": list(rate_limiter.rate_limits.keys()),
            "headers_enabled": rate_limiter.headers_config["include_headers"],
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limit health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }