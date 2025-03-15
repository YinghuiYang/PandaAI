"""
PandaAIQA application entry
"""

import os
import uvicorn
import logging
from pathlib import Path

# makesure the package can be found
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import config
from simple_pandaaiqa.config import HOST, PORT, DEBUG
from simple_pandaaiqa.api import app
from simple_pandaaiqa.utils.helpers import ensure_dir

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup():
    """Set up the application"""
    # ensure the static directory exists
    static_dir = Path(__file__).parent / "static"
    ensure_dir(static_dir)
    
    logger.info(f"Application setup complete, static directory: {static_dir}")

def main():
    """
    Start the PandaAIQA server
    """
    # run setup
    setup()
    
    # start the server
    logger.info(f"Starting PandaAIQA server, listening at {HOST}:{PORT}")
    logger.info("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "simple_pandaaiqa.api:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main() 