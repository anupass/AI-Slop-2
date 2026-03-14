#!/usr/bin/env python3
"""
Sports Betting Bot - Main Entry Point
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from web.app import app
from src.utils import setup_logger
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

logger = setup_logger(__name__)

def main():
    """Main entry point"""
    logger.info("Starting Sports Betting Bot...")
    
    # Start web server
    logger.info("Starting web server...")
    
    try:
        # Print all registered routes for debugging
        logger.info("\n" + "="*60)
        logger.info("REGISTERED FLASK ROUTES:")
        logger.info("="*60)
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            logger.info(f"  {rule.rule:45} [{methods}]")
        logger.info("="*60 + "\n")
        
        # Run Flask app
        logger.info(f"Flask app running on http://{FLASK_HOST}:{FLASK_PORT}")
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()