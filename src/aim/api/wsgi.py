"""
WSGI entry point for the AIM Framework API server.

This module provides the WSGI application for production deployment
with Gunicorn or other WSGI servers.
"""

import os
import asyncio
from aim.api.server import AIMServer
from aim.utils.config import Config
from aim.utils.logger import setup_logging


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask application instance
    """
    # Load configuration
    config_file = os.environ.get('AIM_CONFIG_FILE', 'config/config.json')
    config = Config()
    
    if os.path.exists(config_file):
        config.load_from_file(config_file)
    
    # Override with environment variables
    if os.environ.get('AIM_LOG_LEVEL'):
        config.set('logging.level', os.environ['AIM_LOG_LEVEL'])
    if os.environ.get('AIM_API_HOST'):
        config.set('api.host', os.environ['AIM_API_HOST'])
    if os.environ.get('AIM_API_PORT'):
        config.set('api.port', int(os.environ['AIM_API_PORT']))
    
    # Setup logging
    setup_logging(
        level=config.get("logging.level", "INFO"),
        format_string=config.get("logging.format"),
        log_file=config.get("logging.file"),
        max_file_size=config.get("logging.max_file_size", 10485760),
        backup_count=config.get("logging.backup_count", 5),
    )
    
    # Create server
    server = AIMServer(config)
    
    # Initialize framework asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.framework.initialize())
    finally:
        loop.close()
    
    return server.app


# Create the application instance
application = create_app()

if __name__ == "__main__":
    application.run(debug=False)