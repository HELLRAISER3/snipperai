import os
from rapidocr_onnxruntime import RapidOCR
import logging


logging.basicConfig(level=logging.INFO)

class OCRAction():
    def __init__(self):
        self.engine = RapidOCR()

    def execute(self, image_path: str) -> str:
        """Extract text from an image."""
        text_results, _ = self.engine(image_path)
        
        
        if not text_results:
            return ""
        
        extracted_lines = [line[1] for line in text_results if line and len(line) > 1]
        
        return " ".join(extracted_lines)   


if __name__ == "__main__":
    ocr = OCRAction()

    text = ocr.execute("././buffer/snip_buffer.png")
    logging.log(logging.INFO, "Your extracted text is:\n%s", text)