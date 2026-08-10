import sys
import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.sip import isdeleted 

from snipperai.components.actions import OCRAction, CopyAction, CloseAction, AgentAction
from snipperai.ui.overlay import SnipperOverlay
from snipperai.ui.ocr_result_window import TextResultWindow
from snipperai.ui.agent_window import AgentChatWindow


class HotkeySignal(QObject):
    triggered = pyqtSignal()


class SnipperApp:
    def __init__(self, hotkey: str = "ctrl+shift+s"):
        self.hotkey = hotkey
        self.ocr_action = OCRAction()
        self.agent_action = AgentAction()
        
        self.overlay = None
        self.result_window = None

        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.triggered.connect(self.start_snip)
        
        keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed)

    def _on_hotkey_pressed(self):
        self.hotkey_signal.triggered.emit()

    def create_tray_icon(self, app: QApplication) -> QSystemTrayIcon:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(37, 99, 235))
        
        tray_icon = QSystemTrayIcon(QIcon(pixmap), app)
        tray_icon.setToolTip(f"SnipperAI (Active: {self.hotkey.upper()})")

        menu = QMenu()
        snip_action = menu.addAction("Snip Screen")
        snip_action.triggered.connect(self.start_snip)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Exit SnipperAI")
        quit_action.triggered.connect(app.quit)

        tray_icon.setContextMenu(menu)
        tray_icon.show()
        return tray_icon

    def start_snip(self):
        """Launches the full-screen selection overlay safely."""
        if self.overlay is not None and not isdeleted(self.overlay):
            try:
                self.overlay.close()
            except RuntimeError:
                pass
        
        self.overlay = SnipperOverlay(save_path="./buffer/snip_buffer.png")
        self.overlay.action_requested.connect(self.dispatch_action)
        self.overlay.destroyed.connect(self._on_overlay_destroyed)
        self.overlay.show()

    def _on_overlay_destroyed(self):
        self.overlay = None

    def dispatch_action(self, action_type: str, image_path: str):
        if action_type == "EXPLAIN":
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
    app.setQuitOnLastWindowClosed(False)

    snipper_app = SnipperApp(hotkey="ctrl+shift+s")
    tray_icon = snipper_app.create_tray_icon(app)

    print(f"SnipperAI running in background. Press '{snipper_app.hotkey.upper()}' to capture.")
    sys.exit(app.exec())