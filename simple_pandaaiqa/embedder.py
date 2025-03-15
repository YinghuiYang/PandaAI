"""
Simple Embedder
Uses LM Studio API to generate embeddings
"""

import numpy as np
import logging
import requests
from typing import List
from sentence_transformers import SentenceTransformer

from simple_pandaaiqa.config import EMBEDDING_DIMENSION, LM_STUDIO_API_BASE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Embedder:
    
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("Initialized simple embedder")
    
    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """Normalize vector"""
        norm = np.linalg.norm(vector)
        return vector if norm == 0 else vector / norm
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as a numpy array
        """
        try:
            text = text.lower().strip()
            return self.model.encode(text, normalize_embeddings=True)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            vector = np.random.randn(EMBEDDING_DIMENSION).astype(np.float32)
            return self._normalize(vector)
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Embedding {len(texts)} texts")
        
        return [self.embed_text(text) for text in texts] 