from functools import wraps
import json
from typing import Any, Callable, Optional, TypeVar, cast
from redis import Redis
from datetime import timedelta
import os

# Type variables for better type hints
T = TypeVar('T', bound=Callable[..., Any])

class RedisCache:
    def __init__(self):
        self.redis = Redis.from_url(
            os.getenv('REDIS_CACHE_URL', 'redis://redis-cache:6379/1'),
            decode_responses=True
        )
        self.default_timeout = timedelta(minutes=30)

    def cached(
        self,
        timeout: Optional[int] = None,
        key_prefix: str = '',
        unless: Optional[Callable[..., bool]] = None
    ) -> Callable[[T], T]:
        def decorator(f: T) -> T:
            @wraps(f)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                if unless and unless(*args, **kwargs):
                    return await f(*args, **kwargs)

                cache_key = self._make_cache_key(f, key_prefix, args, kwargs)
                cached_value = self.redis.get(cache_key)

                if cached_value is not None:
                    return json.loads(cached_value)

                value = await f(*args, **kwargs)
                cache_timeout = timeout if timeout is not None else self.default_timeout
                self.redis.setex(
                    cache_key,
                    cache_timeout,
                    json.dumps(value)
                )
                return value

            return cast(T, wrapper)
        return decorator

    def _make_cache_key(
        self,
        f: Callable[..., Any],
        key_prefix: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any]
    ) -> str:
        key_parts = [key_prefix] if key_prefix else []
        key_parts.append(f.__module__ or '')
        key_parts.append(f.__name__)
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ':'.join(key_parts)

    def invalidate(self, pattern: str) -> None:
        """Invalidate all keys matching the pattern."""
        for key in self.redis.scan_iter(pattern):
            self.redis.delete(key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        info = self.redis.info()
        return {
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'keys': info.get('db1', {}).get('keys', 0),
            'memory_used': info.get('used_memory_human', '0B')
        }

# Global cache instance
cache = RedisCache()
