# main.py

import sys
from PyQt6.QtWidgets import QApplication

from snipperai.components.actions import OCRAction, CopyAction, CloseAction, AgentAction
from snipperai.ui.overlay import SnipperOverlay
from snipperai.ui.ocr_result_window import TextResultWindow


class SnipperApp:
    def __init__(self):
        self.ocr_action = OCRAction()
        self.agent_action = AgentAction()
        self.result_window = None

    def start_snip(self):
        self.overlay = SnipperOverlay(save_path="./buffer/snip_buffer.png")
        self.overlay.action_requested.connect(self.dispatch_action)
        self.overlay.show()

    def dispatch_action(self, action_type: str, image_path: str):
        if action_type == "EXPLAIN":
            # Call the agent action and display results
            ai_explanation = self.agent_action.execute(image_path)
            
            self.result_window = TextResultWindow(ai_explanation)
            self.result_window.setWindowTitle("SnipperAI - AI Explanation")
            self.result_window.show()
            self.result_window.raise_()
            self.result_window.activateWindow()

        elif action_type == "OCR":
            extracted_text = self.ocr_action.execute(image_path)
            if not extracted_text or not extracted_text.strip():
                extracted_text = "[No text detected in selected area]"

            self.result_window = TextResultWindow(extracted_text)
            self.result_window.setWindowTitle("SnipperAI - OCR Scan Result")
            self.result_window.show()
            self.result_window.raise_()
            self.result_window.activateWindow()

        elif action_type == "COPY_IMAGE":
            CopyAction.execute(image_path)
            print("Image copied to clipboard successfully!")

        elif action_type == "CLOSE":
            CloseAction.execute()
            print("Snipping cancelled.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    snipper_app = SnipperApp()
    snipper_app.start_snip()
    sys.exit(app.exec())