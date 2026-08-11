import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from snipperai.config import settings


class SettingsDialog(QDialog):
    """Modal settings dialog bound to Pydantic/JSON app configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("SnipperAI - Settings")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._apply_stylesheet()
        self._setup_ui()
        self._load_settings()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F3F4F6;
                color: #111827;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                font-weight: 600;
                font-size: 13px;
                color: #374151;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
            QPushButton#saveBtn {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#saveBtn:hover {
                background-color: #1D4ED8;
            }
            QCheckBox {
                font-size: 13px;
                color: #374151;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- Section 1: OpenRouter API Key ---
        api_group = QGroupBox("API & Authentication (BYOK)")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(10)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-or-v1-...")

        self.toggle_key_btn = QPushButton("Show")
        self.toggle_key_btn.setFixedWidth(60)
        self.toggle_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_key_btn.clicked.connect(self._toggle_key_visibility)

        key_input_layout = QHBoxLayout()
        key_input_layout.addWidget(self.api_key_input)
        key_input_layout.addWidget(self.toggle_key_btn)

        api_layout.addRow(QLabel("OpenRouter Key:"), key_input_layout)
        main_layout.addWidget(api_group)

        # --- Section 2: Preferences ---
        pref_group = QGroupBox("Preferences")
        pref_layout = QVBoxLayout(pref_group)
        pref_layout.setSpacing(10)

        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g. Ctrl+Shift+S")

        hotkey_layout = QFormLayout()
        hotkey_layout.addRow(QLabel("Global Hotkey:"), self.hotkey_input)
        pref_layout.addLayout(hotkey_layout)

        self.autostart_checkbox = QCheckBox("Launch SnipperAI on system startup")
        pref_layout.addWidget(self.autostart_checkbox)

        main_layout.addWidget(pref_group)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("saveBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def _toggle_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("Show")

    def _load_settings(self):
        """Populates UI controls with values loaded from `config.py`."""
        if settings.openrouter_api_key:
            self.api_key_input.setText(settings.openrouter_api_key)

        self.hotkey_input.setText(getattr(settings, "hotkey", "Ctrl+Shift+S"))
        self.autostart_checkbox.setChecked(getattr(settings, "autostart", False))

    def _save_settings(self):
        """Persists settings to disk via `Settings.save_settings()`."""
        api_key = self.api_key_input.text().strip() or None
        hotkey = self.hotkey_input.text().strip() or "Ctrl+Shift+S"
        autostart = self.autostart_checkbox.isChecked()

        try:
            settings.save_settings(
                api_key=api_key,
                hotkey=hotkey,
                autostart=autostart,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving Config", f"Could not write configuration to disk: {e}"
            )