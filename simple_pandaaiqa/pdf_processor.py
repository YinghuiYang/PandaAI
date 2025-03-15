import logging
from typing import List, Dict, Any, Optional
from PyPDF2 import PdfReader
from io import BytesIO

from simple_pandaaiqa.config import CHUNK_SIZE, CHUNK_OVERLAP

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processor class, processes PDF splitting and creates documents"""

    def __init__(
        self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
    ):
        """Initialize PDF processor"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(
            f"Initialized PDF processor, chunk size={chunk_size}, chunk overlap={chunk_overlap}"
        )

    def process_pdf(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process PDF, split it into chunks and create documents

        Args:
            pdf_path: Path to PDF file
            metadata: Optional metadata

        Returns:
            List of documents, each containing text and metadata
        """
        logger.info(f"Processing PDF: {content}")
        metadata = metadata or {}
        chunks = self._split_pdf(content)
        documents = [
            {
                "text": chunk,
                "metadata": {**metadata, "chunk_id": i, "chunk_count": len(chunks)},
            }
            for i, chunk in enumerate(chunks)
        ]
        logger.info(f"Created {len(documents)} documents")
        return documents

    def _split_pdf(self, content: str) -> List[str]:
        """
        Split PDF into multiple chunks based on chunk size and overlap

        Args:
            content: Path to PDF file

        Returns:
            List of text chunks
        """
        reader = PdfReader(BytesIO(content))
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        chunks = []
        start = 0
        text_length = len(full_text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk = full_text[start:end]
            chunks.append(chunk)

            if end == text_length:
                break

            start += self.chunk_size - self.chunk_overlap

        return chunks
