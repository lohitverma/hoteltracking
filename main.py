import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.database import SessionLocal, engine, Base
from backend.models import Hotel, PriceHistory, PriceAlert, CacheEntry, Analytics, User
import uvicorn

# Create database tables
Base.metadata.create_all(bind=engine)

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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Add your API routes here
# ...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=4,
        reload=False,
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
