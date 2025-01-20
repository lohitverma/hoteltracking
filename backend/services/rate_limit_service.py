from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Tuple, List
import time
from redis import Redis
from datetime import datetime
import hashlib
import json

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        # Define rate limit rules
        self.rate_limits = {
            "default": {"rate": 60, "per": 60},  # 60 requests per minute
            "search": {"rate": 30, "per": 60},   # 30 searches per minute
            "auth": {"rate": 5, "per": 900},     # 5 attempts per 15 minutes
            "price_check": {"rate": 100, "per": 3600},  # 100 requests per hour
            "chatbot": {"rate": 20, "per": 60},  # 20 messages per minute
        }
        
        # Endpoint to rate limit mapping
        self.endpoint_limits = {
            "/api/search": "search",
            "/api/hotels/search": "search",
            "/auth/login": "auth",
            "/auth/register": "auth",
            "/api/prices": "price_check",
            "/api/chat": "chatbot",
        }

    def _generate_key(self, request: Request, limit_type: str) -> str:
        """Generate a unique key for rate limiting"""
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0]
        else:
            ip = request.client.host
            
        # Get user ID if authenticated
        user_id = "anonymous"
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
            
        # Create unique key
        key = f"rate_limit:{limit_type}:{ip}:{user_id}"
        return key

    async def is_rate_limited(self, request: Request) -> Tuple[bool, Dict]:
        """Check if request should be rate limited"""
        path = request.url.path
        limit_type = self.endpoint_limits.get(path, "default")
        limit_rules = self.rate_limits[limit_type]
        
        key = self._generate_key(request, limit_type)
        current_time = int(time.time())
        window_start = current_time - limit_rules["per"]
        
        # Use pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Count requests in window
        pipe.zcard(key)
        
        # Set expiry on the key
        pipe.expire(key, limit_rules["per"])
        
        # Execute pipeline
        _, _, request_count, _ = pipe.execute()
        
        # Check if limit exceeded
        is_limited = request_count > limit_rules["rate"]
        
        # Calculate remaining requests and reset time
        remaining = max(0, limit_rules["rate"] - request_count)
        reset_time = current_time + limit_rules["per"]
        
        headers = {
            "X-RateLimit-Limit": str(limit_rules["rate"]),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
        
        return is_limited, headers

    def get_usage_stats(self, request: Request) -> Dict:
        """Get current rate limit usage statistics"""
        stats = {}
        current_time = int(time.time())
        
        for limit_type, rules in self.rate_limits.items():
            key = self._generate_key(request, limit_type)
            window_start = current_time - rules["per"]
            
            # Get request count in current window
            count = self.redis.zcount(key, window_start, current_time)
            
            stats[limit_type] = {
                "limit": rules["rate"],
                "remaining": max(0, rules["rate"] - count),
                "reset": current_time + rules["per"],
                "window_size": rules["per"]
            }
            
        return stats

class RateLimitMiddleware:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path.startswith(("/static/", "/docs", "/redoc")):
            return await call_next(request)
            
        # Check rate limit
        is_limited, headers = await self.rate_limiter.is_rate_limited(request)
        
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "type": "rate_limit_exceeded"
                },
                headers=headers
            )
            
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers.update(headers)
        
        return response
