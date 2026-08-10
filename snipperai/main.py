import sys
from PyQt6.QtWidgets import QApplication

from snipperai.components.ocr import OCR
from snipperai.ui.overlay import SnipperOverlay
from snipperai.ui.result_window import TextResultWindow

class SnipperApp:
    def __init__(self):
        self.ocr = OCR()
        self.result_window = None

    def start_snip(self):
        self.overlay = SnipperOverlay(save_path="./buffer/snip_buffer.png")
        self.overlay.snippet_captured.connect(self.process_snip)
        self.overlay.show()

    def process_snip(self, image_path: str):
        extracted_text = self.ocr.extract_text(image_path)
        
        if not extracted_text.strip():
            extracted_text = "[No text detected in selected area]"

        self.result_window = TextResultWindow(extracted_text)
        self.result_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    snipper_app = SnipperApp()
    
    snipper_app.start_snip()
    
    sys.exit(app.exec())