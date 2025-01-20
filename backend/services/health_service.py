import logging
from typing import Dict, Any, List
import psutil
import aiohttp
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from redis import Redis
import socket

logger = logging.getLogger(__name__)

class HealthService:
    def __init__(self, db_session: Session, redis_client: Redis):
        self.db_session = db_session
        self.redis_client = redis_client
        self.external_services = [
            {
                "name": "amadeus_api",
                "url": "https://api.amadeus.com/v1/health",
                "timeout": 5
            },
            {
                "name": "openai_api",
                "url": "https://api.openai.com/v1/health",
                "timeout": 5
            }
        ]

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            self.db_session.execute(text("SELECT 1"))
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "message": "Database is responding normally"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "response_time": None,
                "message": f"Database error: {str(e)}"
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = datetime.now()
            self.redis_client.ping()
            response_time = (datetime.now() - start_time).total_seconds()
            
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "response_time": response_time,
                "used_memory": info["used_memory_human"],
                "connected_clients": info["connected_clients"],
                "message": "Redis is responding normally"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "response_time": None,
                "message": f"Redis error: {str(e)}"
            }

    async def check_external_services(self) -> List[Dict[str, Any]]:
        """Check external service endpoints"""
        results = []
        async with aiohttp.ClientSession() as session:
            for service in self.external_services:
                try:
                    start_time = datetime.now()
                    async with session.get(
                        service["url"],
                        timeout=service["timeout"]
                    ) as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        results.append({
                            "name": service["name"],
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_time": response_time,
                            "status_code": response.status,
                            "message": "Service is responding normally" if response.status == 200 else f"Service returned status {response.status}"
                        })
                except Exception as e:
                    logger.error(f"External service health check failed for {service['name']}: {str(e)}")
                    results.append({
                        "name": service["name"],
                        "status": "unhealthy",
                        "response_time": None,
                        "status_code": None,
                        "message": f"Service error: {str(e)}"
                    })
        
        return results

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if cpu_percent < 90 and memory.percent < 90 and disk.percent < 90 else "warning",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "status": "healthy" if cpu_percent < 90 else "warning"
                },
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "usage_percent": memory.percent,
                    "status": "healthy" if memory.percent < 90 else "warning"
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "usage_percent": disk.percent,
                    "status": "healthy" if disk.percent < 90 else "warning"
                }
            }
        except Exception as e:
            logger.error(f"System resources check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"System resources check error: {str(e)}"
            }

    def check_network(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Test DNS resolution
            socket.gethostbyname("google.com")
            
            # Test network interfaces
            interfaces = psutil.net_if_stats()
            active_interfaces = {
                name: stats for name, stats in interfaces.items()
                if stats.isup
            }
            
            return {
                "status": "healthy" if active_interfaces else "warning",
                "active_interfaces": len(active_interfaces),
                "interfaces": {
                    name: {
                        "status": "up" if stats.isup else "down",
                        "speed": stats.speed
                    }
                    for name, stats in interfaces.items()
                }
            }
        except Exception as e:
            logger.error(f"Network check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Network check error: {str(e)}"
            }

    async def get_complete_health_status(self) -> Dict[str, Any]:
        """Get complete health status of all components"""
        db_status = await self.check_database()
        redis_status = await self.check_redis()
        external_services_status = await self.check_external_services()
        system_status = self.check_system_resources()
        network_status = self.check_network()
        
        # Determine overall status
        component_statuses = [
            db_status["status"],
            redis_status["status"],
            system_status["status"],
            network_status["status"]
        ] + [service["status"] for service in external_services_status]
        
        if "unhealthy" in component_statuses:
            overall_status = "unhealthy"
        elif "warning" in component_statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_status,
                "redis": redis_status,
                "external_services": external_services_status,
                "system_resources": system_status,
                "network": network_status
            }
        }
