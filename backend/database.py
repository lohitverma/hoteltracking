from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_database_url():
    # First try to get the complete DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Handle Render.com's postgres:// vs postgresql:// issue
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    
    # If no DATABASE_URL, construct from individual components
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hoteltracker")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def create_db_engine():
    database_url = get_database_url()
    logger.info(f"Connecting to database at: {database_url.split('@')[1]}")  # Log only host/db part
    
    return create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        pool_recycle=300
    )

try:
    engine = create_db_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
