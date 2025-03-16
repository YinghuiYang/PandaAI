import logging
from simple_pandaaiqa.config import CHUNK_SIZE, CHUNK_OVERLAP
from typing import List, Dict, Any, Optional
import whisper
import subprocess
import os
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Video processor class, extracts audio with ffmpeg (subprocess) and transcribes using Whisper"""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        whisper_model: str = "base",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model = whisper.load_model(whisper_model)
        logger.info(
            f"Initialized Video processor with Whisper model '{whisper_model}', chunk size={chunk_size}, chunk overlap={chunk_overlap}"
        )

    def process_video(
        self, video_file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        metadata = metadata or {}
        audio_file_path = self._extract_audio(video_file_path)
        text = self._transcribe_audio(audio_file_path)
        chunks = self._split_text(text)
        documents = [
            {
                "text": chunk,
                "metadata": {**metadata, "chunk_id": i, "chunk_count": len(chunks)},
            }
            for i, chunk in enumerate(chunks)
        ]
        logger.info(f"Created {len(documents)} documents from video")
        return documents

    def _extract_audio(self, video_file_path: str) -> str:
        logger.info(f"Extracting audio from video file '{video_file_path}'")
        audio_file_path = tempfile.mktemp(suffix=".wav")
        command = [
            "ffmpeg",
            "-i",
            video_file_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            audio_file_path,
        ]
        try:
            subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            logger.info(f"Audio extracted to '{audio_file_path}'")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFMPEG error: {e.stderr.decode('utf-8', errors='replace')}")
            raise
        return audio_file_path

    def _transcribe_audio(self, audio_file_path: str) -> str:
        logger.info(f"Transcribing audio file: '{audio_file_path}'")
        audio_data = whisper.load_audio(audio_file_path)
        result = self.model.transcribe(audio_data)
        logger.info(f"Transcribed audio: {result}")
        os.unlink(audio_file_path)
        return result["text"]

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
        sentence_ends = {".", "!", "?", "\n"}
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
