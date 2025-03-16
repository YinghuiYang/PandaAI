import io
import logging
import easyocr
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ImageProcessor:
    # Initialize EasyOCR
    def __init__(self, lang_list=["en"]):
        try:
            self.reader = easyocr.Reader(lang_list, gpu=True) # Change this line to use GPU
            logger.info(f"Initialized EasyOCR for languages: {lang_list}")
        except Exception as e:
            logger.error(f"Error initializing EasyOCR: {str(e)}")
            raise

    # Process image by extracting text
    def process_image(self, image_data: bytes):
        try:
            # Load image using PIL and convert to RGB
            # EasyOCR requires RGB images
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            # Convert PIL image to numpy array holds pixel values
            image_np = np.array(image)
            # Then uses EasyOCR to extract text
            results = self.reader.readtext(image_np)
            extracted_text = " ".join([res[1] for res in results])
            logger.info(f"Extracted text: '{extracted_text}'")
            if not extracted_text.strip():
                logger.warning("No meaningful text extracted from image")
                return []
            return [{"text": extracted_text, "metadata": {"source": "image"}}]
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return []