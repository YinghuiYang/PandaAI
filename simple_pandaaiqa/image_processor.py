import io
import logging
import pytesseract
from PIL import Image

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ImageProcessor:
    # Initialize pytesseract
    def __init__(self, lang="eng"):
        self.lang = lang
        logger.info(f"Initialized pytesseract with language: {lang}")

    # Process image by extracting text
    def process_image(self, image_data: bytes):
        try:
            # Load image using PIL and convert to RGB
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

            # Use pytesseract to extract text
            extracted_text = pytesseract.image_to_string(image, lang=self.lang)
            extracted_text = extracted_text.strip()

            logger.info(f"Extracted text: '{extracted_text}'")

            if not extracted_text:
                logger.warning("No meaningful text extracted from image")
                return []

            return [{"text": extracted_text, "metadata": {"source": "image"}}]

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return []
