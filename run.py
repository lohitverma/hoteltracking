import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
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

    # Start server
    logger.info(f"Starting server on port {port}")
    os.system(f"uvicorn main:app --host 0.0.0.0 --port {port}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
