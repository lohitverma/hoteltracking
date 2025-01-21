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
from datadog import statsd
from ddtrace import tracer

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

@tracer.wrap(name='database.connectivity_check')
def check_host_connectivity(host, port, timeout=5):
    """Check if host is reachable"""
    with tracer.trace('database.dns_resolution'):
        try:
            logger.info(f"Resolving DNS for {host}")
            addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            ip = addr_info[0][4][0]
            logger.info(f"DNS resolution successful: {host} -> {ip}")
            statsd.increment('database.dns_resolution.success')
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {host}: {str(e)}")
            statsd.increment('database.dns_resolution.failure')
            return False

    with tracer.trace('database.tcp_connection'):
        try:
            sock = socket.create_connection((host, int(port)), timeout=timeout)
            sock.close()
            logger.info(f"Successfully connected to host {host}:{port}")
            statsd.increment('database.connection.success')
            return True
        except (socket.timeout, socket.gaierror, ConnectionRefusedError) as e:
            logger.error(f"Failed to connect to {host}:{port} - {str(e)}")
            statsd.increment('database.connection.failure')
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to {host}:{port} - {str(e)}")
            statsd.increment('database.connection.error')
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
    # Get individual components
    db_user = os.getenv("POSTGRES_USER", "hoteltracker_user")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST", "dpg-cu7failds78s73arp6j0-a.oregon-postgres.render.com")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hoteltracker")
    
    # Log configuration (without sensitive data)
    logger.info(f"Database Configuration:")
    logger.info(f"Host: {db_host}")
    logger.info(f"Port: {db_port}")
    logger.info(f"Database: {db_name}")
    logger.info(f"User: {db_user}")
    
    # Construct database URL
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Test DNS resolution
    try:
        ip_address = socket.gethostbyname(db_host)
        logger.info(f"Successfully resolved {db_host} to {ip_address}")
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {db_host}: {str(e)}")
    
    # Test TCP connection
    try:
        sock = socket.create_connection((db_host, int(db_port)), timeout=5)
        sock.close()
        logger.info(f"TCP connection test successful to {db_host}:{db_port}")
    except Exception as e:
        logger.error(f"TCP connection test failed: {str(e)}")
    
    return database_url

def create_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with retry logic"""
    retry_count = 0
    last_exception = None
    
    # Get database parameters
    db_user = os.getenv("POSTGRES_USER", "hoteltracker_user")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST", "dpg-cu7failds78s73arp6j0-a")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "hoteltracker")  # Using correct database name
    
    # Log configuration (without sensitive data)
    logger.info(f"Database Configuration:")
    logger.info(f"Host: {db_host}")
    logger.info(f"Port: {db_port}")
    logger.info(f"Database: {db_name}")
    logger.info(f"User: {db_user}")
    
    # Use the exact internal URL format from Render.com
    database_url = os.getenv("DATABASE_URL", f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}")
    
    logger.info("Attempting database connection...")
    
    # Create the engine with specific configuration for Render.com
    engine = create_engine(
        database_url,
        pool_size=1,
        max_overflow=2,
        pool_timeout=30,
        connect_args={
            'connect_timeout': 10,
            'application_name': 'hoteltracker',
            'sslmode': 'require'
        }
    )
    
    # Test connection
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
            logger.info("Database connection successful!")
            return engine
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
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
