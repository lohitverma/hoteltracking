import uvicorn
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

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "10000"))
        logger.info(f"Starting server on port {port}")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            workers=1,
            log_level="info",
            access_log=True,
            use_colors=False,
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
