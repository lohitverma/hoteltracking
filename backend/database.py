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
    # Get database URLs with distinct key names
    internal_database_url = os.getenv("RENDER_INTERNAL_DATABASE_URL")
    database_url = os.getenv("DATABASE_URL")
    
    # Get the database keys with distinct names
    internal_key = os.getenv("RENDER_INTERNAL_DB_KEY")
    external_key = os.getenv("RENDER_EXTERNAL_DB_KEY")
    
    # Log available environment variables (without sensitive data)
    env_vars = {
        'DATABASE_URL exists': bool(database_url),
        'RENDER_INTERNAL_DATABASE_URL exists': bool(internal_database_url),
        'Internal DB Key exists': bool(internal_key),
        'External DB Key exists': bool(external_key),
        'RENDER_EXTERNAL_HOSTNAME': os.getenv('RENDER_EXTERNAL_HOSTNAME'),
        'RENDER_SERVICE_NAME': os.getenv('RENDER_SERVICE_NAME'),
        'RENDER_SERVICE_TYPE': os.getenv('RENDER_SERVICE_TYPE')
    }
    logger.info(f"Environment configuration: {env_vars}")
    
    if internal_database_url and internal_key:
        logger.info("Using RENDER_INTERNAL_DATABASE_URL with internal key")
        database_url = internal_database_url
    elif database_url and external_key:
        logger.info("Using external DATABASE_URL with external key")
    else:
        logger.warning("No database URL or key found, using individual parameters")
        # Construct from individual components
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "hoteltracker")
        
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        logger.info(f"Using constructed URL with host: {db_host}:{db_port}/{db_name}")
    
    # Handle URL format
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Converted postgres:// to postgresql:// in URL")
    
    # Parse and validate URL
    try:
        parsed = parse_db_url(database_url)
        if parsed:
            # Only log non-sensitive parts
            logger.info(f"Database host: {parsed['host']}")
            logger.info(f"Database port: {parsed['port']}")
            logger.info(f"Database name: {parsed['dbname']}")
            
            # Check connectivity
            if check_host_connectivity(parsed['host'], parsed['port']):
                logger.info("Host connectivity check passed")
            else:
                logger.error("Host connectivity check failed")
                
            # Try to resolve host
            try:
                ip = socket.gethostbyname(parsed['host'])
                logger.info(f"Resolved database host to IP: {ip}")
            except socket.gaierror as e:
                logger.error(f"Failed to resolve database host: {str(e)}")
    except Exception as e:
        logger.error(f"Error validating database URL: {str(e)}")
    
    return database_url

@tracer.wrap(name='database.engine_creation')
def create_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with retry logic"""
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            with tracer.trace('database.url_preparation'):
                database_url = get_database_url()
                url_parts = database_url.split('@')
                if len(url_parts) > 1:
                    logger.info(f"Attempting database connection to: {url_parts[1]}")
            
            with tracer.trace('database.engine_initialization'):
                # Create the engine with specific configuration for Render.com
                engine = create_engine(
                    database_url,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    connect_args={
                        'connect_timeout': 30,  # Increased timeout
                        'options': '-c statement_timeout=30000',
                        'sslmode': 'require',
                        'application_name': 'hoteltracker',
                        'keepalives': 1,
                        'keepalives_idle': 30,
                        'keepalives_interval': 10,
                        'keepalives_count': 5
                    }
                )
            
            # Verify connection with detailed error handling
            with tracer.trace('database.connection_verification'):
                try:
                    with engine.connect() as connection:
                        # Test basic connectivity
                        connection.execute("SELECT 1")
                        logger.info("Basic connectivity test passed")
                        
                        # Test database permissions
                        connection.execute("SELECT current_user, current_database()")
                        logger.info("Permission test passed")
                        
                        # Get PostgreSQL version
                        result = connection.execute("SHOW server_version").scalar()
                        logger.info(f"Connected to PostgreSQL version: {result}")
                        
                        # Get current database name
                        result = connection.execute("SELECT current_database()").scalar()
                        logger.info(f"Connected to database: {result}")
                        
                        # Get SSL status
                        result = connection.execute("SHOW ssl").scalar()
                        logger.info(f"SSL status: {result}")
                        
                        statsd.increment('database.connection.success')
                        return engine
                except Exception as e:
                    logger.error(f"Detailed connection test failed: {str(e)}")
                    raise
                
        except exc.OperationalError as e:
            last_exception = e
            retry_count += 1
            statsd.increment('database.connection.retry')
            
            # Log detailed error information
            error_msg = str(e)
            if "could not connect to server" in error_msg:
                logger.error("Network connectivity issue detected")
            elif "password authentication failed" in error_msg:
                logger.error("Authentication failed - check credentials")
            elif "database" in error_msg and "does not exist" in error_msg:
                logger.error("Database does not exist")
            elif "SSL SYSCALL error" in error_msg:
                logger.error("SSL connection issue detected")
            else:
                logger.error(f"Database connection error: {error_msg}")
            
            if retry_count < max_retries:
                logger.warning(f"Database connection attempt {retry_count} failed: {str(e)}")
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                logger.error(f"Last error: {str(e)}")
                statsd.increment('database.connection.failure')
                raise
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {str(e)}")
            statsd.increment('database.connection.error')
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
