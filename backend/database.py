from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
import time

load_dotenv()

logger = logging.getLogger(__name__)

def get_database_url():
    # First try to get the complete DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Handle Render.com's postgres:// vs postgresql:// issue
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")
        return database_url
    
    # If no DATABASE_URL, construct from individual components
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hoteltracker")
    
    constructed_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Using constructed database URL with host: {db_host}:{db_port}/{db_name}")
    return constructed_url

def create_db_engine(max_retries=5, retry_interval=5):
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            database_url = get_database_url()
            # Only log the non-sensitive parts of the URL
            url_parts = database_url.split('@')
            if len(url_parts) > 1:
                logger.info(f"Attempting database connection to: {url_parts[1]}")
            
            engine = create_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    'connect_timeout': 10,
                    'options': '-c statement_timeout=30000'
                }
            )
            
            # Verify connection
            with engine.connect() as connection:
                connection.execute("SELECT 1")
                logger.info("Database connection successful!")
                return engine
                
        except Exception as e:
            last_exception = e
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Database connection attempt {retry_count} failed: {str(e)}")
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                logger.error(f"Last error: {str(e)}")
                raise

# Initialize engine with retry logic
try:
    engine = create_db_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Database initialization failed: {str(e)}")
    raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
