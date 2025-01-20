from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging
import json
import os
import time
from dotenv import load_dotenv
import database
import cache
import logging
from hotel_apis.analytics_routes import router as analytics_router
from hotel_apis.city_routes import router as city_router
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.securityheaders import SecurityHeadersMiddleware

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hotel Tracker API",
    description="""
    🏨 A modern API for tracking hotel prices and availability across multiple platforms.
    
    ## Features
    
    * 🔍 Real-time hotel search across multiple providers
    * 📊 Price analytics and historical data
    * 🔔 Price alert notifications
    * 📍 Location-based hotel recommendations
    * 📱 Mobile-friendly API design
    
    ## Getting Started
    
    1. Use the `/api/cities` endpoint to search for cities
    2. Use `/api/hotels/search` to find hotels in your chosen city
    3. Track prices using `/api/hotels/{hotel_id}/prices`
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Hotel Tracker Support",
        "url": "https://hoteltracker.org/support",
        "email": "support@hoteltracker.org",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
if os.getenv("ENVIRONMENT") == "production":
    # Force HTTPS
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "hoteltracker.org",
            "api.hoteltracker.org",
            "www.hoteltracker.org",
            "hotel-tracker-api.onrender.com"
        ]
    )

# Security headers
app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy={
        "default-src": "'self'",
        "img-src": ["'self'", "data:", "https:"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
    },
    strict_transport_security={"max-age": 31536000, "includeSubDomains": True},
    x_frame_options="DENY",
    x_content_type_options="nosniff",
    x_xss_protection="1; mode=block",
    referrer_policy="strict-origin-when-cross-origin"
)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')

# Add custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record request metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    # Record latency
    REQUEST_LATENCY.observe(time.time() - start_time)
    
    # Record system metrics
    MEMORY_USAGE.set(psutil.Process().memory_info().rss)
    CPU_USAGE.set(psutil.cpu_percent())
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path
            }
        }
    )

class SearchParams(BaseModel):
    city: str
    checkin: str
    checkout: str
    guests: int
    rooms: int = 1
    timezone: Optional[str]

@app.get("/")
async def root():
    """
    🏠 Welcome to Hotel Tracker API
    
    Returns a welcome message and basic API information.
    """
    return {
        "message": "Welcome to Hotel Tracker API",
        "version": "1.0.0",
        "docs_url": "/api/docs",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/locations/search")
async def search_locations(
    query: str,
    limit: Optional[int] = 10
):
    """
    Search for locations (cities, regions) by name
    """
    try:
        # Use cache if available
        cache_key = f"location_search:{query}:{limit}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        # Query database
        result = await database.search_locations(query, limit)
        
        # Cache the result
        await cache.set(cache_key, json.dumps(result), expire=3600)
        
        return result
    except Exception as e:
        logger.error(f"Error searching locations: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching locations")

@app.get("/api/hotels/search")
async def search_hotels(
    city: str,
    checkin: str,
    checkout: str,
    guests: int = 2,
    rooms: int = 1
):
    """
    Search for hotels in a specific city
    """
    try:
        # Validate dates
        try:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
            if checkout_date <= checkin_date:
                raise ValueError("Checkout date must be after checkin date")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Use cache if available
        cache_key = f"hotel_search:{city}:{checkin}:{checkout}:{guests}:{rooms}"
        cached_result = await cache.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        # Query database
        result = await database.search_hotels(city, checkin, checkout, guests, rooms)
        
        # Cache the result
        await cache.set(cache_key, json.dumps(result), expire=1800)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching hotels: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching hotels")

@app.get("/health")
async def health_check():
    """
    💓 API Health Check
    
    Checks the health status of all system components.
    """
    status = {
        "status": "healthy",
        "timestamp": int(time()),
        "version": "1.0.0"
    }
    
    try:
        await database.database.execute("SELECT 1")
    except Exception as e:
        status["status"] = "unhealthy"
        status["error"] = str(e)

    try:
        await cache.redis.ping()
    except Exception as e:
        status["status"] = "unhealthy"
        status["error"] = str(e)

    return status

@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/health")
async def health_check():
    """
    💓 API Health Check
    
    Checks the health status of all system components.
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": "unknown",
            "redis": "unknown",
            "celery": "unknown"
        }
    }
    
    try:
        await database.database.execute("SELECT 1")
        status["components"]["database"] = "healthy"
    except Exception as e:
        status["components"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"

    try:
        await cache.redis.ping()
        status["components"]["redis"] = "healthy"
    except Exception as e:
        status["components"]["redis"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"

    try:
        celery_inspect = app.celery_app.control.inspect()
        if celery_inspect.active():
            status["components"]["celery"] = "healthy"
        else:
            status["components"]["celery"] = "no workers available"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["celery"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"

    return status

app.include_router(analytics_router)
app.include_router(city_router)
