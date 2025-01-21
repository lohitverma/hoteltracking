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
from sqlalchemy.engine.url import make_url

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
    """Get the appropriate database URL based on environment"""
    # Try internal URL first (faster within Render's network)
    internal_url = os.getenv("INTERNAL_DATABASE_URL")
    external_url = os.getenv("EXTERNAL_DATABASE_URL")
    fallback_url = os.getenv("DATABASE_URL")  # For backward compatibility
    
    urls_to_try = []
    
    if internal_url:
        urls_to_try.append(("internal", internal_url))
    if external_url:
        urls_to_try.append(("external", external_url))
    if fallback_url:
        urls_to_try.append(("fallback", fallback_url))
        
    if not urls_to_try:
        raise ValueError(
            "No database URL configured. Please set either INTERNAL_DATABASE_URL, "
            "EXTERNAL_DATABASE_URL, or DATABASE_URL environment variable."
        )
    
    return urls_to_try

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

def create_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with retry logic and URL fallback"""
    last_exception = None
    urls_to_try = get_database_url()
    
    for url_type, database_url in urls_to_try:
        logger.info(f"Attempting connection using {url_type} URL...")
        
        # Parse URL for logging (without exposing credentials)
        try:
            parsed_url = make_url(database_url)
            logger.info(f"Connection info ({url_type}):")
            logger.info(f"User: {parsed_url.username}")
            logger.info(f"Host: {parsed_url.host}")
            logger.info(f"Database: {parsed_url.database}")
        except Exception as e:
            logger.error(f"Error parsing {url_type} URL: {str(e)}")
            continue
        
        # Try to connect with retries
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Creating database engine (attempt {retry_count + 1}/{max_retries})...")
                engine = create_engine(
                    database_url,
                    pool_size=1,
                    max_overflow=2,
                    pool_timeout=30,
                    connect_args={
                        'connect_timeout': 10,
                        'application_name': 'hoteltracker',
                        'sslmode': 'require',
                        'keepalives': 1,
                        'keepalives_idle': 30,
                        'keepalives_interval': 10,
                        'keepalives_count': 5
                    }
                )
                
                # Test the connection
                success, info = test_connection(engine)
                if success:
                    logger.info(f"Successfully connected using {url_type} URL!")
                    logger.info(f"PostgreSQL version: {info['version']}")
                    logger.info(f"Connected as: {info['user']}")
                    logger.info(f"Database: {info['database']}")
                    return engine
                    
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                logger.warning(f"Connection attempt {retry_count + 1} failed: {error_msg}")
                
                if "password authentication failed" in error_msg:
                    logger.error(f"Authentication failed for {url_type} URL")
                    break  # Don't retry auth failures
                    
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                    
        logger.error(f"All attempts failed for {url_type} URL")
    
    # If we get here, all URLs failed
    error_msg = str(last_exception) if last_exception else "Unknown error"
    logger.error("All database connection attempts failed!")
    logger.error(f"Last error: {error_msg}")
    
    if "could not connect to server" in error_msg:
        logger.error("Could not reach the database server. Please check:")
        logger.error("1. The database service is running")
        logger.error("2. The host is correct")
        logger.error("3. Network connectivity is available")
    elif "password authentication failed" in error_msg:
        logger.error("Authentication failed. Please check:")
        logger.error("1. The database username is correct")
        logger.error("2. The database password is correct")
    elif "SSL SYSCALL error" in error_msg:
        logger.error("SSL connection error. Please check:")
        logger.error("1. SSL is properly configured")
        logger.error("2. The connection is not being blocked by a firewall")
    
    raise Exception("Failed to connect to database using any available URL")

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
