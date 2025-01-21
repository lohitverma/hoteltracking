from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
import time
import socket
import subprocess
import sys

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_psql_check(host, port, user, dbname):
    """Run psql command to check database connection"""
    try:
        cmd = f'psql "host={host} port={port} dbname={dbname} user={user} sslmode=require" -c "SELECT 1;"'
        logger.info(f"Running connection test: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        logger.info(f"psql test output: {result.stdout}")
        if result.stderr:
            logger.error(f"psql test error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running psql check: {str(e)}")
        return False

def check_host_connectivity(host, port, timeout=5):
    """Check if host is reachable"""
    try:
        # Try DNS resolution first
        try:
            logger.info(f"Resolving DNS for {host}")
            addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            ip = addr_info[0][4][0]
            logger.info(f"DNS resolution successful: {host} -> {ip}")
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {host}: {str(e)}")
            return False

        # Try TCP connection
        sock = socket.create_connection((host, int(port)), timeout=timeout)
        sock.close()
        logger.info(f"Successfully connected to host {host}:{port}")
        return True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError) as e:
        logger.error(f"Failed to connect to {host}:{port} - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error connecting to {host}:{port} - {str(e)}")
        return False

def parse_db_url(url):
    """Parse database URL into components"""
    try:
        # Remove postgresql:// prefix
        clean_url = url.replace('postgresql://', '')
        # Split into credentials and host parts
        creds, rest = clean_url.split('@')
        user, password = creds.split(':')
        # Split host and database
        host_port, dbname = rest.split('/')
        # Split host and port if port exists
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = '5432'
        
        return {
            'user': user,
            'password': password,
            'host': host,
            'port': port,
            'dbname': dbname
        }
    except Exception as e:
        logger.error(f"Error parsing database URL: {str(e)}")
        return None

def get_database_url():
    """Get and validate database URL"""
    # First try to get the complete DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    internal_database_url = os.getenv("RENDER_INTERNAL_DATABASE_URL")
    
    # Log available environment variables (without sensitive data)
    env_vars = {
        'DATABASE_URL exists': bool(database_url),
        'RENDER_INTERNAL_DATABASE_URL exists': bool(internal_database_url),
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
        'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
        'POSTGRES_DB': os.getenv('POSTGRES_DB')
    }
    logger.info(f"Environment configuration: {env_vars}")
    
    if internal_database_url:
        logger.info("Using RENDER_INTERNAL_DATABASE_URL")
        database_url = internal_database_url
    elif database_url:
        logger.info("Using DATABASE_URL")
    else:
        logger.warning("No DATABASE_URL or RENDER_INTERNAL_DATABASE_URL found, using individual parameters")
    
    if database_url:
        # Handle Render.com's postgres:// vs postgresql:// issue
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            logger.info("Converted postgres:// to postgresql:// in database URL")
        
        # Parse and validate database URL
        db_params = parse_db_url(database_url)
        if db_params:
            logger.info(f"Checking connectivity to database host: {db_params['host']}:{db_params['port']}")
            if check_host_connectivity(db_params['host'], db_params['port']):
                # Try psql connection
                if run_psql_check(db_params['host'], db_params['port'], db_params['user'], db_params['dbname']):
                    logger.info("Database connection test successful")
                else:
                    logger.error("Database connection test failed")
        
        return database_url
    
    # If no DATABASE_URL, construct from individual components
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hoteltracker")
    
    # Check host connectivity
    logger.info(f"Checking connectivity to database host: {db_host}:{db_port}")
    check_host_connectivity(db_host, db_port)
    
    constructed_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"Using constructed database URL with host: {db_host}:{db_port}/{db_name}")
    return constructed_url

def create_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with retry logic"""
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
                    'options': '-c statement_timeout=30000',
                    'sslmode': 'require'  # Enable SSL for Render.com
                }
            )
            
            # Verify connection
            with engine.connect() as connection:
                connection.execute("SELECT 1")
                logger.info("Database connection successful!")
                return engine
                
        except exc.OperationalError as e:
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
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {str(e)}")
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
