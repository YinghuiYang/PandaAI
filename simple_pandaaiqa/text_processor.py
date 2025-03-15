"""
Text processor module for PandaAIQA
Handles text splitting and document creation
"""

import logging
from typing import List, Dict, Any, Optional

from simple_pandaaiqa.config import CHUNK_SIZE, CHUNK_OVERLAP

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextProcessor:
    """Text processor class, processes text splitting and creates documents"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """Initialize text processor"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Initialized text processor, chunk size={chunk_size}, chunk overlap={chunk_overlap}")
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process text, split it into chunks and create documents
        
        Args:
            text: Text to process
            metadata: Optional metadata
            
        Returns:
            List of documents, each containing text and metadata
        """
        if not text.strip():
            logger.warning("Received empty text for processing")
            return []
        
        logger.info(f"Processing text, length={len(text)}")
        metadata = metadata or {}
        chunks = self._split_text(text)
        documents = [{"text": chunk, "metadata": {**metadata, "chunk_id": i, "chunk_count": len(chunks)}} for i, chunk in enumerate(chunks)]
        logger.info(f"Created {len(documents)} documents")
        return documents
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into multiple chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        sentence_ends = {'.', '!', '?', '\n'}
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                for i in range(min(50, end - start)):
                    if text[end - i - 1] in sentence_ends:
                        end -= i
                        break
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else end
        logger.info(f"Text split into {len(chunks)} chunks")
        return chunks 