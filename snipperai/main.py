import sys
import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QProcess, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.sip import isdeleted

from snipperai.components.settings.autostart import set_autostart
from snipperai.config import settings
from snipperai.cloud.agent import SnipperAgent
from snipperai.components.actions import OCRAction, CopyAction, CloseAction, AgentAction
from snipperai.components.actions.settings_action import SettingsAction
from snipperai.ui.overlay import SnipperOverlay
from snipperai.ui.ocr_result_window import TextResultWindow
from snipperai.ui.agent_window import AgentChatWindow
from snipperai.ui.onboarding import OnboardingWizard

class HotkeySignal(QObject):
    triggered = pyqtSignal()


class SnipperApp:
    def __init__(self):
        self.current_hotkey = settings.hotkey.lower()
        self.ocr_action = OCRAction()
        self.agent_action = AgentAction()

        self.overlay = None
        self.result_window = None
        self.tray_icon = None

        self.hotkey_signal = HotkeySignal()
        self.hotkey_signal.triggered.connect(self.start_snip)

        self._bind_hotkey(self.current_hotkey)

    def _bind_hotkey(self, hotkey: str):
        """Clears existing hotkeys and binds the newly specified shortcut."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        try:
            keyboard.add_hotkey(hotkey, self._on_hotkey_pressed)
            self.current_hotkey = hotkey
            if self.tray_icon:
                self.tray_icon.setToolTip(f"SnipperAI (Active: {self.current_hotkey.upper()})")
            print(f"[SnipperAI] Active hotkey: {self.current_hotkey.upper()}")
        except Exception as e:
            print(f"[Hotkey Error] Failed to bind '{hotkey}': {e}", file=sys.stderr)

    def _on_hotkey_pressed(self):
        self.hotkey_signal.triggered.emit()

    def create_tray_icon(self, app: QApplication) -> QSystemTrayIcon:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(37, 99, 235))

        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), app)
        self.tray_icon.setToolTip(f"SnipperAI (Active: {self.current_hotkey.upper()})")

        menu = QMenu()

        snip_action = menu.addAction("Snip Screen")
        snip_action.triggered.connect(self.start_snip)

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

        menu.addSeparator()

        quit_action = menu.addAction("Exit SnipperAI")
        quit_action.triggered.connect(app.quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        return self.tray_icon

    def restart_application():
        """Restarts the current Python process cleanly."""
        process = QProcess()
        process.startDetached(sys.executable, sys.argv)
        QApplication.quit()

    def open_settings(self):
        """Opens settings dialog and updates active hotkeys if changed."""
        action = SettingsAction()
        saved = action.execute()

        if saved and settings.hotkey.lower() != self.current_hotkey:
            print(f"[Settings] Hotkey changed to: {settings.hotkey.lower()}")
            self._bind_hotkey(settings.hotkey.lower())
        if saved and getattr(settings, "autostart", None) != getattr(settings, "autostart", None):
            print(f"[Settings] Autostart changed.")
            set_autostart(getattr(settings, "autostart", None))
        if saved:
            self.agent_action = AgentAction(agent=SnipperAgent())

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

        elif action_type == "SETTINGS":
            self.open_settings()

        elif action_type == "CLOSE":
            CloseAction.execute()
            print("Snipping cancelled.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # DEV
    if "--reset-onboarding" in sys.argv:
        settings.first_launch = True
    # DEV
    
    if settings.first_launch:
        wizard = OnboardingWizard()
        if wizard.exec() != OnboardingWizard.DialogCode.Accepted:
            sys.exit(0)

    snipper_app = SnipperApp()
    tray_icon = snipper_app.create_tray_icon(app)

    print(f"SnipperAI background process active ({snipper_app.current_hotkey.upper()}).")
    sys.exit(app.exec())