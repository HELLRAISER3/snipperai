# main.py

import sys
from PyQt6.QtWidgets import QApplication

from snipperai.components.actions import OCRAction, CopyAction, CloseAction, AgentAction
from snipperai.ui.overlay import SnipperOverlay
from snipperai.ui.ocr_result_window import TextResultWindow
from snipperai.ui.agent_window import AgentChatWindow  # Imported new agent chat UI


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
            # Instantiate and display the interactive Agent Chat Window
            self.result_window = AgentChatWindow(
                image_path=image_path, 
                agent_action=self.agent_action
            )
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