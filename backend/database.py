import os
import time
import logging
from sqlalchemy import create_engine, MetaData, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from urllib.parse import urlparse
from dotenv import load_dotenv
import socket
import subprocess
import sys
from datadog import statsd
from ddtrace import tracer

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(url, max_retries=5, retry_interval=5):
    """Wait for database to become available."""
    parsed = urlparse(url)
    logger.info(f"Attempting to connect to database at {parsed.hostname}")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(url)
            engine.connect()
            logger.info("Successfully connected to database!")
            return engine
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_interval} seconds...")
                logger.debug(f"Error details: {str(e)}")
                time.sleep(retry_interval)
            else:
                logger.error("Failed to connect to database after maximum retries")
                raise

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
    """Get database URL with fallback logic."""
    internal_url = os.getenv("INTERNAL_DATABASE_URL")
    external_url = os.getenv("EXTERNAL_DATABASE_URL")
    
    if not internal_url and not external_url:
        raise ValueError("No database URL configured. Set INTERNAL_DATABASE_URL or EXTERNAL_DATABASE_URL")
    
    urls_to_try = []
    if internal_url:
        urls_to_try.append(("internal", internal_url))
    if external_url:
        urls_to_try.append(("external", external_url))
    
    last_error = None
    for url_type, url in urls_to_try:
        try:
            logger.info(f"Attempting connection using {url_type} URL...")
            parsed = urlparse(url)
            logger.info(f"Connection info ({url_type}):")
            logger.info(f"User: {parsed.username}")
            logger.info(f"Host: {parsed.hostname}")
            logger.info(f"Database: {parsed.path[1:]}")  # Remove leading /
            engine = wait_for_db(url)
            logger.info(f"Successfully connected using {url_type} URL")
            return engine
        except Exception as e:
            last_error = e
            logger.warning(f"Failed to connect using {url_type} URL: {str(e)}")
    
    raise last_error

# Create database engine
try:
    engine = get_database_url()
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()
metadata = MetaData()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection(engine):
    """Test database connection and return version info"""
    try:
        with engine.connect() as conn:
            version = conn.execute("SELECT version();").scalar()
            user = conn.execute("SELECT current_user;").scalar()
            database = conn.execute("SELECT current_database();").scalar()
            return True, {
                "version": version,
                "user": user,
                "database": database
            }
    except Exception as e:
        return False, str(e)
