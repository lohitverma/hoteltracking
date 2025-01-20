import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import psutil
import time
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, port: int = 8000):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'status']
        )
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation']
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'status']
        )
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits'
        )
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses'
        )
        
        # Business metrics
        self.hotel_searches_total = Counter(
            'hotel_searches_total',
            'Total hotel searches',
            ['city']
        )
        self.price_alerts_total = Counter(
            'price_alerts_total',
            'Total price alerts',
            ['action', 'status']
        )
        self.chatbot_queries_total = Counter(
            'chatbot_queries_total',
            'Total chatbot queries',
            ['intent']
        )
        
        # System metrics
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes'
        )
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes'
        )
        
        # Start metrics server
        start_http_server(port)
        
        # Start background tasks
        asyncio.create_task(self._collect_system_metrics())
        
    def track_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """Track HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def track_db_query(
        self,
        operation: str,
        status: str,
        duration: float
    ):
        """Track database query metrics"""
        self.db_queries_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        self.db_query_duration_seconds.labels(
            operation=operation
        ).observe(duration)
        
    def track_cache_operation(
        self,
        operation: str,
        status: str,
        hit: Optional[bool] = None
    ):
        """Track cache operation metrics"""
        self.cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        if hit is not None:
            if hit:
                self.cache_hits_total.inc()
            else:
                self.cache_misses_total.inc()
                
    def track_hotel_search(self, city: str):
        """Track hotel search metrics"""
        self.hotel_searches_total.labels(city=city).inc()
        
    def track_price_alert(self, action: str, status: str):
        """Track price alert metrics"""
        self.price_alerts_total.labels(
            action=action,
            status=status
        ).inc()
        
    def track_chatbot_query(self, intent: str):
        """Track chatbot query metrics"""
        self.chatbot_queries_total.labels(intent=intent).inc()
        
    async def _collect_system_metrics(self):
        """Background task to collect system metrics"""
        while True:
            try:
                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory_usage.set(memory.used)
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.system_disk_usage.set(disk.used)
                
                await asyncio.sleep(15)  # Collect every 15 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {str(e)}")
                await asyncio.sleep(60)  # Retry after 1 minute
                
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        return {
            "http_requests": {
                "total": self.http_requests_total._value.sum(),
                "by_endpoint": dict(self.http_requests_total._value._metrics)
            },
            "cache": {
                "hits": self.cache_hits_total._value.sum(),
                "misses": self.cache_misses_total._value.sum(),
                "hit_ratio": (
                    self.cache_hits_total._value.sum() /
                    (self.cache_hits_total._value.sum() + self.cache_misses_total._value.sum())
                    if (self.cache_hits_total._value.sum() + self.cache_misses_total._value.sum()) > 0
                    else 0
                )
            },
            "business": {
                "searches": self.hotel_searches_total._value.sum(),
                "alerts": self.price_alerts_total._value.sum(),
                "chatbot_queries": self.chatbot_queries_total._value.sum()
            },
            "system": {
                "memory_usage_gb": self.system_memory_usage._value.get() / (1024 ** 3),
                "cpu_usage_percent": self.system_cpu_usage._value.get(),
                "disk_usage_gb": self.system_disk_usage._value.get() / (1024 ** 3)
            }
        }
