import os
import sys
import logging
import socket
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def check_port_availability(port):
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        available = True
    except socket.error:
        available = False
    finally:
        sock.close()
    return available

def log_system_info():
    """Log system information."""
    logger.info("System Information:")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Available memory: {psutil.virtual_memory().available / (1024 * 1024):.2f} MB")
    logger.info(f"CPU count: {psutil.cpu_count()}")

def main():
    # Log system information
    log_system_info()

    # Log environment variables (excluding sensitive data)
    env_vars = {k: v for k, v in os.environ.items() if not any(s in k.lower() for s in ['key', 'secret', 'password', 'token'])}
    logger.info(f"Environment variables: {env_vars}")

    # Get port
    port = os.environ.get('PORT', '10000')
    logger.info(f"PORT environment variable: {port}")

    # Convert port to int
    try:
        port = int(port)
        logger.info(f"Converted port to integer: {port}")
    except ValueError as e:
        logger.error(f"Failed to convert PORT to integer: {e}")
        port = 10000
        logger.info(f"Using default port: {port}")

    # Check port availability
    if check_port_availability(port):
        logger.info(f"Port {port} is available")
    else:
        logger.warning(f"Port {port} is not available")
        # List processes using the port
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                for conn in proc.info.get('connections', []):
                    if conn.laddr.port == port:
                        logger.warning(f"Process using port {port}: {proc.info}")
        except Exception as e:
            logger.error(f"Error checking processes: {e}")

    # Start server
    logger.info(f"Starting server on port {port}")
    os.system(f"uvicorn main:app --host 0.0.0.0 --port {port} --log-level debug")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
