from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.orm import Session
import aioredis
import pickle

from models import CacheEntry
from services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(
        self,
        db: Session,
        monitoring_service: MonitoringService,
        redis_url: str = "redis://localhost:6379"
    ):
        self.db = db
        self.monitoring_service = monitoring_service
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            # Try Redis first
            value = await self.redis.get(key)
            if value:
                self.monitoring_service.track_cache_operation("get", "hit", True)
                return pickle.loads(value.encode())
                
            # Try database
            cache_entry = self.db.query(CacheEntry).filter(
                CacheEntry.key == key,
                CacheEntry.expires_at > datetime.utcnow()
            ).first()
            
            if cache_entry:
                # Store in Redis for next time
                await self.redis.set(
                    key,
                    pickle.dumps(cache_entry.value),
                    ex=int((cache_entry.expires_at - datetime.utcnow()).total_seconds())
                )
                self.monitoring_service.track_cache_operation("get", "hit", True)
                return cache_entry.value
                
            self.monitoring_service.track_cache_operation("get", "miss", False)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.monitoring_service.track_cache_operation("get", "error")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: timedelta
    ) -> bool:
        """Set value in cache"""
        try:
            # Store in Redis
            await self.redis.set(
                key,
                pickle.dumps(value),
                ex=int(ttl.total_seconds())
            )
            
            # Store in database
            expires_at = datetime.utcnow() + ttl
            cache_entry = self.db.query(CacheEntry).filter(
                CacheEntry.key == key
            ).first()
            
            if cache_entry:
                cache_entry.value = value
                cache_entry.expires_at = expires_at
            else:
                cache_entry = CacheEntry(
                    key=key,
                    value=value,
                    expires_at=expires_at
                )
                self.db.add(cache_entry)
                
            self.db.commit()
            self.monitoring_service.track_cache_operation("set", "success")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            self.monitoring_service.track_cache_operation("set", "error")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            # Delete from Redis
            await self.redis.delete(key)
            
            # Delete from database
            self.db.query(CacheEntry).filter(
                CacheEntry.key == key
            ).delete()
            
            self.db.commit()
            self.monitoring_service.track_cache_operation("delete", "success")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            self.monitoring_service.track_cache_operation("delete", "error")
            return False
            
    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            # Clear Redis
            await self.redis.flushdb()
            
            # Clear database
            self.db.query(CacheEntry).delete()
            self.db.commit()
            
            self.monitoring_service.track_cache_operation("clear", "success")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            self.monitoring_service.track_cache_operation("clear", "error")
            return False
            
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            # Get Redis stats
            redis_info = await self.redis.info()
            redis_keys = await self.redis.dbsize()
            
            # Get database stats
            total_entries = self.db.query(CacheEntry).count()
            expired_entries = self.db.query(CacheEntry).filter(
                CacheEntry.expires_at <= datetime.utcnow()
            ).count()
            active_entries = total_entries - expired_entries
            
            return {
                "redis": {
                    "keys": redis_keys,
                    "used_memory": redis_info["used_memory"],
                    "hits": redis_info["keyspace_hits"],
                    "misses": redis_info["keyspace_misses"],
                    "uptime": redis_info["uptime_in_seconds"]
                },
                "database": {
                    "total_entries": total_entries,
                    "active_entries": active_entries,
                    "expired_entries": expired_entries
                }
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {}
            
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            # Delete expired entries from database
            expired = self.db.query(CacheEntry).filter(
                CacheEntry.expires_at <= datetime.utcnow()
            ).delete()
            
            self.db.commit()
            self.monitoring_service.track_cache_operation("cleanup", "success")
            return expired
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
            self.monitoring_service.track_cache_operation("cleanup", "error")
            return 0
            
    async def get_or_set(
        self,
        key: str,
        value_func: Callable[[], Any],
        ttl: timedelta
    ) -> Any:
        """Get value from cache or compute and store it"""
        value = await self.get(key)
        if value is not None:
            return value
            
        value = await value_func()
        await self.set(key, value, ttl)
        return value
