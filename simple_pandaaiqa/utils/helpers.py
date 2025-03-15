"""
PandaAIQA Helper Functions
"""

import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dir(directory: str) -> None:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def extract_file_extension(filename: str) -> str:
    """
    Extract file extension from filename
    
    Args:
        filename: Filename
        
    Returns:
        File extension (lowercase)
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()[1:]  # Remove dot and convert to lowercase 