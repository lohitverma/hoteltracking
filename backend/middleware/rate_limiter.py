from typing import Optional
from fastapi import Request, Response
import time
from redis import Redis
import os
from fastapi.responses import JSONResponse

class RateLimiter:
    def __init__(self):
        self.redis = Redis.from_url(
            os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            decode_responses=True
        )
        
        # Rate limit configurations
        self.rate_limits = {
            "default": {"requests": 100, "window": 3600},  # 100 requests per hour
            "search": {"requests": 20, "window": 60},      # 20 searches per minute
            "booking": {"requests": 5, "window": 3600},    # 5 bookings per hour
            "premium": {"requests": 1000, "window": 3600}, # 1000 requests per hour for premium users
        }

    async def check_rate_limit(
        self,
        request: Request,
        limit_key: str = "default"
    ) -> Optional[Response]:
        # Get client IP and endpoint
        client_ip = request.client.host
        endpoint = request.url.path
        
        # Get user type from request (default to standard)
        user_type = request.headers.get("X-User-Type", "standard")
        
        # Use premium limits for premium users
        if user_type == "premium":
            limit_key = "premium"
        
        # Get rate limit configuration
        limit_config = self.rate_limits.get(limit_key, self.rate_limits["default"])
        requests_limit = limit_config["requests"]
        window = limit_config["window"]
        
        # Create Redis key
        redis_key = f"rate_limit:{client_ip}:{endpoint}:{limit_key}"
        
        # Get current count and timestamp
        current_time = int(time.time())
        window_start = current_time - window
        
        # Remove old requests
        self.redis.zremrangebyscore(redis_key, 0, window_start)
        
        # Count requests in current window
        request_count = self.redis.zcard(redis_key)
        
        if request_count >= requests_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": window - (current_time - int(self.redis.zrange(redis_key, 0, 0)[0]))
                }
            )
        
        # Add current request
        self.redis.zadd(redis_key, {str(current_time): current_time})
        self.redis.expire(redis_key, window)
        
        # Add rate limit headers
        remaining = requests_limit - request_count - 1
        reset_time = current_time + window
        
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(requests_limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
        
        return None

    async def add_headers(self, request: Request, response: Response):
        """Add rate limit headers to response"""
        if hasattr(request.state, "rate_limit_headers"):
            for header, value in request.state.rate_limit_headers.items():
                response.headers[header] = value

# Global rate limiter instance
rate_limiter = RateLimiter()
