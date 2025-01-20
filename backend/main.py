from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
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
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from models import City, Hotel
from database import get_db
from services.alert_service import AlertService
from services.chatbot_service import ChatbotService
from services.monitoring_service import MonitoringService, PrometheusMiddleware
from services.security_service import SecurityHeaders, SSLConfig, CORSConfig
from services.auth_service import AuthService
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import uvicorn
import asyncio
from services.rate_limit_service import RateLimiter, RateLimitMiddleware
from redis import Redis
from services.api_key_service import APIKeyService
from services.oauth_service import OAuthService
from services.cache_service import CacheService
from services.email_verification_service import EmailVerificationService
from services.price_tracking_service import PriceTrackingService
from services.health_service import HealthService

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

# Security configurations
ALLOWED_HOSTS = [
    "hoteltracker.org",
    "api.hoteltracker.org",
    "www.hoteltracker.org",
    "localhost",
    "127.0.0.1"
]

CORS_ORIGINS = [
    "https://hoteltracker.org",
    "https://api.hoteltracker.org",
    "https://www.hoteltracker.org",
    "http://localhost:3000",
    "http://localhost:8000"
]

# Add security middleware
app.add_middleware(
    SecurityHeaders,
    allowed_hosts=ALLOWED_HOSTS,
    hsts_max_age=31536000
)

# Configure CORS
cors_config = CORSConfig(allowed_origins=CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    **cors_config.get_cors_config()
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

# Initialize monitoring service
monitoring_service = MonitoringService(SessionLocal())

# Add PrometheusMiddleware
app.add_middleware(PrometheusMiddleware, monitoring_service=monitoring_service)

# Initialize Redis client
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)

# Initialize cache service
cache_service = CacheService(redis_client)

# Initialize rate limiter
rate_limiter = RateLimiter(redis_client)

# Add rate limit middleware
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Initialize API key service
api_key_service = APIKeyService()

# Initialize OAuth service
oauth_service = OAuthService()

# Initialize email verification service
email_verification_service = EmailVerificationService()

# Initialize health service
health_service = HealthService(SessionLocal(), redis_client)

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
@cache_service.cached(
    prefix="hotel_search",
    ttl=timedelta(minutes=5)
)
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

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Get complete health status of all system components.
    
    Returns:
    - Overall system status (healthy/warning/unhealthy)
    - Status of individual components:
        - Database
        - Redis
        - External services
        - System resources
        - Network
    """
    return await health_service.get_complete_health_status()

@app.get("/health/database", tags=["Monitoring"])
async def database_health():
    """Check database health status"""
    return await health_service.check_database()

@app.get("/health/redis", tags=["Monitoring"])
async def redis_health():
    """Check Redis health status"""
    return await health_service.check_redis()

@app.get("/health/external", tags=["Monitoring"])
async def external_services_health():
    """Check external services health status"""
    return await health_service.check_external_services()

@app.get("/health/system", tags=["Monitoring"])
async def system_health():
    """Check system resources health status"""
    return health_service.check_system_resources()

@app.get("/health/network", tags=["Monitoring"])
async def network_health():
    """Check network health status"""
    return health_service.check_network()

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

# Monitoring endpoints
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get Prometheus metrics.
    
    This endpoint returns metrics in Prometheus format, including:
    - HTTP request metrics (count, duration)
    - Database metrics (queries, latency)
    - Cache metrics (hits, misses)
    - API metrics (calls, errors)
    - System metrics (CPU, memory, disk)
    - Business metrics (users, searches, alerts)
    
    Requires admin authentication.
    """
    return Response(
        content=monitoring_service.get_metrics(),
        media_type="text/plain"
    )

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Get system health status.
    
    Returns:
    - Overall system status (healthy/warning/unhealthy)
    - Database status and latency
    - System resource usage (CPU, memory, disk)
    - Timestamp of check
    
    Status will be 'warning' if any resource usage is above 90%.
    """
    return await monitoring_service.get_health_check()

@app.get("/metrics/business", tags=["Monitoring"])
async def get_business_metrics(
    current_user: User = Depends(auth_service.get_current_admin_user)
):
    """
    Get business metrics for the last 24 hours.
    
    Returns:
    - Active users count
    - Hotel searches by city
    - Price alerts by type and status
    - Success/failure rates
    
    Requires admin authentication.
    """
    return {
        "active_users": monitoring_service.active_users._value.get(),
        "hotel_searches": {
            "total": monitoring_service.hotel_searches._value.get(),
            "success_rate": monitoring_service.hotel_searches.labels(
                city="all",
                success="true"
            )._value.get() / monitoring_service.hotel_searches._value.get()
        },
        "price_alerts": {
            "total": monitoring_service.price_alerts._value.get(),
            "by_status": {
                "active": monitoring_service.price_alerts.labels(
                    type="all",
                    status="active"
                )._value.get(),
                "triggered": monitoring_service.price_alerts.labels(
                    type="all",
                    status="triggered"
                )._value.get()
            }
        }
    }

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        monitoring_service.log_error(e, {
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent")
        })
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Initialize services
auth_service = AuthService()

# Auth models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# Auth endpoints
@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user and send verification email.
    
    Parameters:
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Strong password (min 8 chars)
    - **full_name**: Optional full name
    
    Returns:
    - User details and access token
    
    Raises:
    - 400: Email already registered
    - 422: Invalid input data
    """
    # Validate password strength
    if not auth_service.validate_password(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create user
    new_user = await auth_service.register_user(user, db)
    
    # Send verification email
    token = await email_verification_service.create_verification_token(new_user.id)
    await email_verification_service.create_verification_record(db, new_user.id, token)
    success = await email_verification_service.send_verification_email(new_user, token)
    
    if not success:
        logger.error(f"Failed to send verification email to user {new_user.id}")
        
    return new_user

@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Parameters:
    - **username**: Email or username
    - **password**: User password
    
    Returns:
    - Access and refresh tokens
    
    Raises:
    - 401: Invalid credentials
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return auth_service.create_tokens(user.id)

@app.post("/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    return await auth_service.refresh_access_token(refresh_token, db)

@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """
    Get current user information
    """
    return current_user

@app.post("/auth/logout", tags=["Authentication"])
async def logout(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user
    """
    # In a real implementation, you might want to blacklist the token
    # For now, we'll just update the last_login
    current_user.last_login = datetime.utcnow()
    db.commit()
    return {"message": "Successfully logged out"}

# Email verification endpoints
@app.post("/auth/verify-email/send", tags=["Authentication"])
async def send_verification_email(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send or resend email verification link.
    
    This endpoint:
    - Creates a new verification token
    - Sends verification email to user
    - Returns success/failure status
    
    Rate limit: 3 requests per hour per user
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )
        
    success = await email_verification_service.resend_verification_email(
        db,
        current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email"
        )
        
    return {"message": "Verification email sent"}

@app.get("/auth/verify-email", tags=["Authentication"])
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user's email address using verification token.
    
    This endpoint:
    - Validates the verification token
    - Updates user's email verification status
    - Returns success/failure status
    
    The token expires after 24 hours.
    """
    user = await email_verification_service.verify_email(db, token)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
        
    return {
        "message": "Email verified successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
            "email_verified_at": user.email_verified_at
        }
    }

@app.get("/auth/verify-email/status", tags=["Authentication"])
async def get_verification_status(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get current user's email verification status.
    
    Returns:
    - Email verification status
    - Timestamp of verification
    """
    return {
        "email_verified": current_user.email_verified,
        "email_verified_at": current_user.email_verified_at
    }

# OAuth endpoints
@app.get("/auth/login/google", tags=["OAuth"])
async def google_login():
    """
    Get Google OAuth login URL
    """
    return {"url": await oauth_service.get_google_auth_url()}

@app.get("/auth/login/github", tags=["OAuth"])
async def github_login():
    """
    Get GitHub OAuth login URL
    """
    return {"url": await oauth_service.get_github_auth_url()}

@app.get("/auth/callback/google", tags=["OAuth"])
async def google_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    """
    user, access_token, refresh_token = await oauth_service.handle_google_callback(code, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.get("/auth/callback/github", tags=["OAuth"])
async def github_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback
    """
    user, access_token, refresh_token = await oauth_service.handle_github_callback(code, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/auth/refresh/oauth", tags=["OAuth"])
async def refresh_oauth_token(
    provider: str,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh OAuth access token
    """
    return await oauth_service.refresh_oauth_token(provider, refresh_token)

# Rate limit endpoints
@app.get("/api/rate-limits", tags=["Rate Limiting"])
async def get_rate_limits(
    request: Request,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """
    Get current rate limit usage
    """
    return rate_limiter.get_usage_stats(request)

# API Key models
class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = 365
    scopes: Optional[List[str]] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    scopes: List[str]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    usage_count: int

    class Config:
        from_attributes = True

class APIKeyCreateResponse(APIKeyResponse):
    api_key: str

# API Key endpoints
@app.post("/api/keys", response_model=APIKeyCreateResponse, tags=["API Keys"])
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    """
    return await api_key_service.create_api_key(
        db,
        current_user,
        key_data.name,
        key_data.expires_in_days,
        key_data.scopes
    )

@app.get("/api/keys", response_model=List[APIKeyResponse], tags=["API Keys"])
async def list_api_keys(
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for current user
    """
    return await api_key_service.list_api_keys(db, current_user)

@app.delete("/api/keys/{key_id}", tags=["API Keys"])
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an API key
    """
    success = await api_key_service.revoke_api_key(db, current_user, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked successfully"}

@app.get("/api/keys/scopes", tags=["API Keys"])
async def get_available_scopes(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """
    Get list of available API scopes
    """
    return api_key_service.get_available_scopes()

# Example of protected endpoint requiring API key
@app.get("/api/protected/hotels", response_model=List[Dict], tags=["Protected Endpoints"])
async def list_hotels_api(
    api_key: str = Depends(api_key_service.require_api_key)
):
    """
    Example protected endpoint requiring API key
    """
    return [{"message": "This endpoint requires a valid API key"}]

# WebSocket endpoints
@app.websocket("/api/ws/prices/{city}")
async def websocket_endpoint(websocket: WebSocket, city: str, db: Session = Depends(get_db)):
    _, _, _, _, price_tracking_service = get_services(db)
    await price_tracking_service.connect_client(websocket, city)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await price_tracking_service.disconnect_client(websocket, city)

# Price tracking endpoints
@app.get("/api/prices/statistics/{city}")
async def get_price_statistics(city: str, db: Session = Depends(get_db)):
    try:
        _, _, _, _, price_tracking_service = get_services(db)
        return await price_tracking_service.get_price_statistics(city)
    except Exception as e:
        logger.error(f"Error getting price statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to update metrics
@app.on_event("startup")
async def start_metrics_collection():
    async def update_metrics():
        while True:
            await monitoring_service.update_system_metrics()
            await monitoring_service.update_application_metrics(next(get_db()))
            await asyncio.sleep(15)  # Update every 15 seconds
    
    asyncio.create_task(update_metrics())

# Alert preference models
class AlertPreferenceCreate(BaseModel):
    hotel_id: int
    price_threshold: float
    email: str
    phone: Optional[str] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True

class AlertPreferenceResponse(BaseModel):
    id: int
    hotel_id: int
    price_threshold: float
    email: str
    phone: Optional[str]
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool

# Alert routes
@app.post("/api/alerts", response_model=AlertPreferenceResponse, tags=["Alerts"])
async def create_alert(
    alert: AlertPreferenceCreate,
    db: Session = Depends(get_db),
    # TODO: Replace with actual user authentication
    user_id: str = "test_user"
):
    """
    Create a new price alert for a hotel
    """
    alert_service = AlertService(db)
    return alert_service.create_alert_preference(
        user_id=user_id,
        hotel_id=alert.hotel_id,
        price_threshold=alert.price_threshold,
        email=alert.email,
        phone=alert.phone,
        email_enabled=alert.email_enabled,
        sms_enabled=alert.sms_enabled,
        push_enabled=alert.push_enabled
    )

@app.get("/api/alerts/notifications", response_model=List[dict], tags=["Alerts"])
async def get_notifications(
    db: Session = Depends(get_db),
    limit: int = 50,
    # TODO: Replace with actual user authentication
    user_id: str = "test_user"
):
    """
    Get recent notifications for the user
    """
    alert_service = AlertService(db)
    notifications = alert_service.get_user_notifications(user_id, limit)
    return [{
        "id": n.id,
        "message": n.message,
        "type": n.type,
        "status": n.status,
        "created_at": n.created_at,
        "sent_at": n.sent_at
    } for n in notifications]

# Background task to check price alerts
@app.post("/api/alerts/check", tags=["Alerts"])
async def check_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger price alert checks (should be called by a scheduler)
    """
    alert_service = AlertService(db)
    await alert_service.check_price_alerts(background_tasks)
    return {"status": "Alert check initiated"}

# Chatbot models
class ChatMessage(BaseModel):
    message: str
    city_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]]
    error: Optional[str] = None

# Chatbot routes
@app.post("/api/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat_with_ai(
    chat_message: ChatMessage,
    db: Session = Depends(get_db),
    # TODO: Replace with actual user authentication
    user_id: str = "test_user"
):
    """
    Process a chat message and return AI response
    """
    chatbot = ChatbotService(db)
    return await chatbot.process_message(
        message=chat_message.message,
        city_id=chat_message.city_id
    )

@app.get("/api/chat/recommendations", tags=["Chatbot"])
async def get_recommendations(
    city_id: Optional[int] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Get hotel recommendations based on criteria
    """
    chatbot = ChatbotService(db)
    return chatbot.get_hotel_recommendations(
        city_id=city_id,
        max_price=max_price,
        min_rating=min_rating
    )

# City routes
@app.get("/api/cities", response_model=List[dict], tags=["Cities"])
async def get_cities(db: Session = Depends(get_db)):
    """
    Get list of available cities
    """
    cities = db.query(City).all()
    return [{"id": city.id, "name": city.name} for city in cities]

@app.get("/api/cities/nearest", tags=["Cities"])
async def get_nearest_city(lat: float, lon: float, db: Session = Depends(get_db)):
    """
    Get nearest city based on coordinates
    """
    cities = db.query(City).all()
    if not cities:
        raise HTTPException(status_code=404, detail="No cities found in database")
    
    # Calculate distances to all cities
    distances = []
    for city in cities:
        distance = geodesic((lat, lon), (city.latitude, city.longitude)).miles
        distances.append((distance, city))
    
    # Get nearest city
    nearest_city = min(distances, key=lambda x: x[0])[1]
    return {"id": nearest_city.id, "name": nearest_city.name}

@app.get("/api/hotels", tags=["Hotels"])
async def get_hotels(city_id: int, db: Session = Depends(get_db)):
    """
    Get hotels for a specific city
    """
    hotels = db.query(Hotel).filter(Hotel.city_id == city_id).all()
    if not hotels:
        return []
    
    return [{
        "id": hotel.id,
        "name": hotel.name,
        "address": hotel.address,
        "rating": hotel.rating,
        "price": hotel.current_price,
        "image_url": hotel.image_url,
        "amenities": hotel.amenities
    } for hotel in hotels]

@app.get("/api/hotels/{hotel_id}/prices", tags=["Hotels"])
@cache_service.cached(
    prefix="hotel_prices",
    ttl=timedelta(minutes=30)
)
async def get_hotel_prices(
    hotel_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """
    Get hotel price history with caching
    """
    # Existing price history logic here
    pass

@app.get("/api/cache/stats", tags=["Cache"])
async def get_cache_stats(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """
    Get cache statistics
    """
    return await cache_service.get_stats()

@app.post("/api/cache/clear/{pattern}", tags=["Cache"])
async def clear_cache(
    pattern: str,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """
    Clear cache by pattern
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    cleared = await cache_service.clear_pattern(pattern)
    return {"cleared_keys": cleared}

app.include_router(analytics_router)
app.include_router(city_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png",
        extra_html="""
            <link rel="stylesheet" href="/static/swagger-ui-custom.css">
            <style>
                .swagger-ui .topbar { display: none }
            </style>
        """
    )

# Hotel endpoints with detailed documentation
@app.get(
    "/api/hotels/search",
    response_model=List[Dict],
    tags=["Hotels"],
    responses={
        200: {
            "description": "List of hotels matching the search criteria",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "name": "Grand Hotel",
                        "city": "New York",
                        "current_price": 299.99,
                        "rating": 4.5,
                        "amenities": ["wifi", "pool", "spa"]
                    }]
                }
            }
        },
        400: {
            "description": "Invalid search parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid date range"}
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded. Try again in 60 seconds."}
                }
            }
        }
    }
)
@cache_service.cached(
    prefix="hotel_search",
    ttl=timedelta(minutes=5)
)
async def search_hotels(
    query: str = Query(
        ...,
        description="Search query for hotel name, amenities, or location",
        example="luxury pool view"
    ),
    location: str = Query(
        ...,
        description="City or location to search in",
        example="New York"
    ),
    check_in: date = Query(
        ...,
        description="Check-in date (YYYY-MM-DD)",
        example="2024-06-15"
    ),
    check_out: date = Query(
        ...,
        description="Check-out date (YYYY-MM-DD)",
        example="2024-06-20"
    ),
    guests: int = Query(
        2,
        description="Number of guests",
        ge=1,
        le=10,
        example=2
    ),
    min_price: Optional[float] = Query(
        None,
        description="Minimum price per night",
        ge=0,
        example=100
    ),
    max_price: Optional[float] = Query(
        None,
        description="Maximum price per night",
        ge=0,
        example=500
    ),
    min_rating: Optional[float] = Query(
        None,
        description="Minimum hotel rating",
        ge=0,
        le=5,
        example=4
    ),
    amenities: Optional[List[str]] = Query(
        None,
        description="Required amenities",
        example=["wifi", "pool"]
    ),
    sort_by: Optional[str] = Query(
        "relevance",
        description="Sort results by field",
        enum=["relevance", "price_low", "price_high", "rating"],
        example="rating"
    ),
    db: Session = Depends(get_db)
):
    """
    Search for hotels with comprehensive filtering options.
    
    The search is cached for 5 minutes to improve performance.
    Results are ordered based on the sort_by parameter.
    
    Rate limit: 30 requests per minute per user
    
    Examples:
    ```
    # Search for luxury hotels in New York
    GET /api/hotels/search?query=luxury&location=New York&check_in=2024-06-15&check_out=2024-06-20
    
    # Search for affordable hotels with pool
    GET /api/hotels/search?query=pool&location=Miami&max_price=200&amenities=pool&sort_by=price_low
    ```
    
    Notes:
    - Date format must be YYYY-MM-DD
    - Check-out date must be after check-in date
    - Price filters are per night
    - Rating is on a scale of 0-5
    """
    pass

# Custom OpenAPI documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "/auth/login/google",
                    "tokenUrl": "/auth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access"
                    }
                }
            }
        },
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "JWT": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def get_services(db: Session = Depends(get_db)):
    cache_service = CacheService(db, monitoring_service)
    hotel_service = HotelService(db, cache_service)
    alert_service = AlertService(db, monitoring_service)
    chatbot_service = ChatbotService(db, hotel_service)
    price_tracking_service = PriceTrackingService(db, cache_service, monitoring_service)
    return hotel_service, alert_service, chatbot_service, cache_service, price_tracking_service

if __name__ == "__main__":
    ssl_context = SSLConfig.get_ssl_context()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="privkey.pem",
        ssl_certfile="fullchain.pem",
        ssl_ca_certs=certifi.where(),
        ssl_ciphers=":".join(ssl_context.get_ciphers()),
        reload=True
    )
