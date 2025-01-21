import os
import sys
import logging
import socket
import psutil
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.database import SessionLocal, engine, Base, wait_for_db
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hotel Tracker API",
    description="API for tracking hotel prices and managing alerts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that verifies database connection."""
    try:
        # Verify database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": "1.0.0",
            "database": str(e)
        }

if __name__ == "__main__":
    try:
        # Get port
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting server on port {port}")
        
        # Start server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            access_log=True,
            log_level="info",
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
